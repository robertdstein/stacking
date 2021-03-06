import numpy as np
import matplotlib.pyplot as plt
import random
import copy
import os
import cPickle as pickle
import scipy as scp

from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.integrate import romberg, quad
from scipy.optimize import minimize_scalar
from scipy.optimize import minimize
from scipy.optimize import curve_fit
from scipy.stats import norm
from scipy.stats import poisson
from scipy.interpolate import interp1d
from scipy.optimize import bisect
from numpy.polynomial import polynomial
from numpy.polynomial.polynomial import polyval
from scipy.optimize import brentq
import scipy as scp
from scipy import stats

plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['savefig.dpi'] = 400
plt.rcParams['legend.fancybox'] = True
plt.rcParams['legend.frameon'] = False
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.serif'] = 'Times New Roman'
plt.rcParams['font.cursive'] = 'Times New Roman'
plt.rcParams['lines.linewidth'] = 1.


class Sensitivity():
    def __init__(self, path='test_stat_results/test_setup',
                 plot_path='plots/LikelihoodLandscape/test_setup',
                 plotting=False, upper_limit=False, config="Fast_with_fit"):
        """Initialises default values for all attributes

        :param path: Root results_path for reading pickle files
        :param plot_path: Root results_path for saving plots
        :param plotting: Boolean for whether to produce plots
        :param upper_limit:
        :param config:
        """

        path += "_" + config + "_"
        plot_path += config + "_"

        self.path = path + "TS.pkl"
        self.fit_params_path = path + "params.pkl"
        self.fit_status_path = path + "convergence.pkl"
        self.plot_path = plot_path
        self.plotting = plotting
        self.UpperLimit = upper_limit

        self.alpha = 50. * 1.e-2
        self.beta = 90. * 1.e-2

        self.all_data = dict()
        self.read_test_stat()
        self.generate_distributions()

        self.all_data['det_chance'] = dict()
        self.all_data['det_chance_func'] = dict()

    def read_test_stat(self, ):
        """Reads test statistics from pickle file, and assigns them as an
        attribute. Prints a warning if pickle file does not exist.
        """
        if os.path.isfile(self.path):
            pkl_file = open(self.path, 'rb')
            test_stat_results = pickle.load(pkl_file)
            pkl_file.close()
            self.test_stat_results = test_stat_results
        else:
            print self.path, ' does not exist'

    def generate_distributions(self, ):
        """Initialises default dictionary values for attributes. Loops over
        test stat results, and fills dictionaries with entries.
        """
        # Initialise empty dictionaries

        self.all_data['test_stat_all_unsorted'] = dict()
        self.all_data['test_stat_sorted'] = dict()
        self.all_data['test_stat_sorted_all'] = dict()
        self.all_data['cumu_dist_normed'] = dict()
        self.all_data['weights'] = dict()
        self.all_data['NTrials'] = dict()

        # Loop over flux values

        for k in self.test_stat_results.keys():

            #Save both sorted and unsorted TS

            self.all_data['test_stat_all_unsorted'][k] = self.test_stat_results[k]
            all_test_stat_sorted = np.sort(self.test_stat_results[k])
            self.all_data['test_stat_sorted_all'][k] = all_test_stat_sorted

            # ***************************************************************
            self.all_data['test_stat_sorted'][k] = np.unique(
                all_test_stat_sorted)
            weights = np.array([float(np.sum(all_test_stat_sorted == i))
                                for i in np.unique(all_test_stat_sorted)])

            self.all_data['weights'][k] = weights
            self.all_data['cumu_dist_normed'][k] = (
                np.cumsum(weights) / np.sum(weights))
            self.all_data['NTrials'][k] = len(self.test_stat_results[k])

    def find_test_stat_threshold(self, ):
        """

        :return:
        """
        if len(self.all_data['test_stat_all_unsorted']) > 1:
            data = self.all_data['test_stat_all_unsorted'][0]
            mask = data > 0.
            fraction = np.sum(mask) / float(len(mask))
            print'Fraction of underfluctuations is ',
            print '{0:.2f}'.format(1. - fraction)
            fit_res = scp.stats.chi2.fit(data[mask], df=2., floc=0., fscale=1.)

            # if False:
            #     x = np.linspace(0., 50., 1.e5)
            #     y = scp.stats.chi2.pdf(x, fit_res[0]) * fraction
            #     plt.figure()
            #     plt.hist(data, bins=50, lw=2, histtype='step',
            #         normed=True, color='black', label='BG Test Stat')
            #     plt.plot(x, y, lw=2, color='red',
            #         label=r'$\chi^2$ fit, df={0:6.2f}'.format(fit_res[0]))
            #     plt.semilogy()
            #     plt.xlim(0., 1.e1)
            #     plt.ylim(1.e-3, 1.e0)
            #     plt.grid()
            #     plt.xlabel(r"$\lambda$")
            #     plt.legend(loc='best', fancybox=True, framealpha=1.)
            #     plt.savefig('plots/test_stats/MyCodeTestStatBG.pdf')
            #     plt.show()

            if self.alpha > 0.1:
                self.TestStatThreshold = np.percentile(
                    self.all_data['test_stat_sorted_all'][0.0],
                    (1. - self.alpha) * 1.e2)
            else:
                f = lambda x: scp.stats.chi2.sf(x, fit_res[0]) * \
                    fraction - self.alpha
                AlphaSigma = bisect(f, 0., 50.)
                self.TestStatThreshold = AlphaSigma
                if True:
                    from matplotlib import cm
                    col = [cm.gist_rainbow(x) for x in np.linspace(0, 1, 20)]
                    x = np.linspace(0., 50., 1.e5)
                    y = scp.stats.chi2.sf(x, fit_res[0]) * fraction
                    y[0] += (1. - fraction)
                    fig, ax1 = plt.subplots()
                    plt.gcf().subplots_adjust(bottom=0.15, top=0.8, left=0.15)
                    plt.axhline(
                        self.alpha, color=col[1], lw=1, label=r'Significance')
                    plt.axvline(AlphaSigma, lw=1, color=col[1])
                    plt.hist(
                        data, bins=100, lw=2, histtype='step', normed=True,
                        color='black', label='BG Test Stat', cumulative=-1)
                    plt.plot(x, y, lw=2, color=col[15],
                             label=r'$\chi^2$ fit, df={0:6.2f}'.format(fit_res[0]))
                    plt.semilogy()
                    plt.xlim(0., 3.e1)
                    plt.ylim(1.e-7, 1.e0)
                    plt.xlabel(r"$\lambda$")
                    plt.ylabel(r"$\int_{\lambda}^\infty P(\lambda^\prime)" +
                               "\mathrm{d}\lambda^\prime$")
                    plt.legend(loc='best', fancybox=True, framealpha=1.)
                    plt.savefig('plots/test_stats/MyCodeTestStatBG_withSens.pdf')
                    plt.show()

            if self.UpperLimit:
                self.TestStatThreshold = input("Measured lambda? ")

            return True

        else:
            return False


    def plot_TS_distribution(self):

        for k in sorted(self.all_data['test_stat_all_unsorted'].keys()):
            data = self.all_data['test_stat_all_unsorted'][k]

            path = self.plot_path + "ts_" + str(k) + ".pdf"
            plt.figure()
            plt.hist(data, bins=20, lw=2, histtype='step',color='black', label='Test Stat')
            plt.yscale("log")
            plt.grid()
            plt.xlabel(r"$\lambda$")
            plt.savefig(path)
            plt.close()



    def FindDetectionChance(self, ):
        self.all_data['DetChanceFunc'] = {}
        self.all_data['DetChance'] = {}
        for k in sorted(self.all_data['test_stat_sorted'].keys()):
            data = self.all_data['test_stat_sorted'][k]

            if k == 0:
                self.all_data['DetChance'][k] = self.alpha
            else:

                # print k,
                # print self.all_data['test_stat_sorted'][k],
                # print self.all_data['cumu_dist_normed'][k]

                try:

                    g = interp1d(self.all_data['test_stat_sorted'][k],
                        self.all_data['cumu_dist_normed'][k],
                        bounds_error=False, fill_value=0.)
                    f = lambda x: 1. - g(x)
                    self.all_data['DetChanceFunc'][k] = f
                    self.all_data['DetChance'][k] = f(self.TestStatThreshold)
                except ValueError:
                    pass

    def sens_interpolation_function(self, x, a):
        value = (1. - np.exp(-np.log10(a) * x)) *\
            (1. - self.alpha) + self.alpha
        return value

    def InterpolateDetectionChance(self, ):
        raw_x = np.sort(np.array(self.all_data['test_stat_sorted_all'].keys()))
        raw_y = np.array([self.all_data['DetChance'][k] for k in raw_x])
        raw_weights = np.array([self.all_data['NTrials'][k] for k in raw_x])

        # mask = raw_y < 0.99
        # if (len(raw_y[mask]) > 4) and (max(raw_y[mask]) > 0.9):
        #     x = raw_x[mask]
        #     y = raw_y[mask]
        #     weights = raw_weights[mask]

        # else:
        x = raw_x
        y = raw_y
        weights = raw_weights

        self.DetChanceInterpolation = interp1d(raw_x, raw_y, kind='linear')

        PolyParams = np.polyfit(x, y, 3, w=weights)
        self.DetChancePolyFit = lambda z: np.polyval(PolyParams, z)
        self.DetChanceMyFit = scp.optimize.curve_fit(
            self.sens_interpolation_function, x, y, sigma=1. / weights
        )[0]

    def find_sensitivity(self, ):

        flux_scale_min = np.min(self.all_data['test_stat_sorted_all'].keys()[:])
        flux_scale_max = np.max(self.all_data['test_stat_sorted_all'].keys())
        x = np.linspace(flux_scale_min, flux_scale_max, 1.e3)

        f = lambda x: self.DetChancePolyFit(x) - self.beta
        f2 = lambda x: self.DetChanceInterpolation(x) - self.beta
        f3 = lambda x: self.sens_interpolation_function(
            x, self.DetChanceMyFit) - self.beta


        if self.plotting:
            # print(self.results_path)

            plt.figure()

            for k in self.all_data['DetChance'].keys():
                plt.scatter(k, self.all_data['DetChance'][k], color='black')

            plt.plot(x, self.DetChanceInterpolation(x), lw=2,
                     color='blue', label='Interpolation')
            plt.plot(x, self.DetChancePolyFit(x), lw=2,
                     color='red', label='PolyFit')
            plt.plot(x, self.sens_interpolation_function(x, self.DetChanceMyFit),
                     lw=2, color='black',
                     label=r'$(1-\exp(-ax))+{0:6.2f}$'.format(1. - self.alpha))
            plt.axhline(y=self.beta, lw=2)
#            plt.grid()
            plt.xlim(flux_scale_min, flux_scale_max)
            plt.ylim(.2, 1.)

            try:
                plt.axvline(x=brentq(f, flux_scale_min, flux_scale_max),
                            lw=2, color='red')
            except:
                pass
            try:
                plt.axvline(x=brentq(f2, flux_scale_min, flux_scale_max),
                            lw=2, color='blue')
            except:
                pass
            try:
                plt.axvline(x=brentq(f3, flux_scale_min, flux_scale_max),
                            lw=2, color='black')
            except:
                pass
            plt.legend(loc='best', fancybox=True, framealpha=1.)
            plt.xlabel(r"Flux strength $E^2 \mathrm{d}N /" +
                       "\mathrm{d}E$ [ TeV cm$^{-2}$ s$^{-1}$]")
            plt.xlabel(r'Signal Flux Strength')
            plt.ylabel(r'chance for $\lambda$ over threshold')

            save_path = str(self.plot_path) + 'sens.pdf'
            save_dir = os.path.dirname(save_path)
            if not os.path.isdir(save_dir):
                os.makedirs(save_dir)

            plt.savefig(save_path)
            plt.close()

        fits = dict()
        try:
            index = np.argwhere(np.diff(
                np.sign(f(x))) != 0).reshape(-1)[0]
            fits["polynom"] = x[index]

            print 'Polynom: ', '{0:.2f}'.format(fits["polynom"])
        except:
            print 'Polynom: Failed'
            fits["polynom"] = np.nan
        try:
            index = np.argwhere(np.diff(
                np.sign(f2(x))) != 0).reshape(-1)[0]
            fits["interpolation"] = x[index]
            print 'Interpolation: ', '{0:.2f}'.format(fits["interpolation"])
        except:
            print 'Interpolation: Failed'
            fits["interpolation"] = np.nan
        try:
            fits["mine"] = brentq(f3, flux_scale_min, flux_scale_max)
            print'My Interpolation: ', '{0:.2f}'.format(fits["mine"])
        except:
            print 'My Interpolation: Failed'
            fits["mine"] = np.nan
        print ''
        return fits

    def ComputeP_Value(self, ):
        MeasuredLambda = input("Measured lambda? ")
        x = np.sort(self.test_stat_results[0])
        print(('p-value: ' + str(100. - stats.percentileofscore(x,
            MeasuredLambda, kind='weak')) + '%'))
        print(('p-value: ' + str(100. - stats.percentileofscore(x,
            MeasuredLambda, kind='strict')) + '%'))

    def CreateSensitivyAllInOne(self, ):
        self.generate_distributions()
        self.find_test_stat_threshold()
        self.FindDetectionChance()
        self.InterpolateDetectionChance()
        fits = self.find_sensitivity()
        if self.plotting:
            self.plot_TS_distribution()
            self.plot_fit_results()
        self.check_fit_status()
        return fits

    def pValueFunction(self, MeasuredLambda):
        self.generate_distributions()
        x = np.sort(self.test_stat_results[0])
        correct_p_value = 100. - stats.percentileofscore(
            x, MeasuredLambda, kind='strict')
        #mask = x > 0.
        #fraction = np.sum(mask) / float(len(mask))
        #fit_res = scp.stats.chi2.fit(x[mask], df=2., floc=0., fscale=1.)
        #
        ##Is this redundant?
        #if MeasuredLambda == 0.:
            #FitPValue = 100.
        #else:
            #FitPValue = scp.stats.chi2.pdf(MeasuredLambda, fit_res[0]) * \
                #fraction * 100.
        return correct_p_value

    def plot_fit_results(self):
        with open(self.fit_params_path, 'rb') as pkl_file:
            fit_params = pickle.load(pkl_file)
            for x, data in fit_params.iteritems():
                n_params = data.shape[1]
                plt.figure()

                for i, row in enumerate(data.T):
                    vals = list(row[0])
                    median = np.median(vals)

                    ax = plt.subplot(n_params, 1, i+1)
                    plt.hist(vals, bins=20)
                    ax.axvline(median, linestyle="--", color="k")

                save_path = self.plot_path + "params_" + str(x) + ".pdf"

                plt.savefig(save_path)
                plt.close()

    def check_fit_status(self):
        with open(self.fit_status_path, 'rb') as pkl_file:
            fit_status = pickle.load(pkl_file)
            for x, data in sorted(fit_status.iteritems()):

                n_fail = float(len(data[data > 0.]))
                n = float(len(data))
                frac = n_fail/n
                if frac > 0.5:
                    print "For", x, "we have",
                    print frac, "failue in fit convergence."

