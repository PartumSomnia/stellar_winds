#====================================================#
#
# This is the main file, containg my project
# reading, interpolating, analysing OPAL tables
# reading, plotting properites of the star from
# sm.data files of BEC output and more)
#
#====================================================#

#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------MAIN-LIBRARIES-----------------------------------------------------
import sys
import pylab as pl
from matplotlib import cm
import numpy as np
from ply.ctokens import t_COMMENT
from scipy import interpolate

from sklearn.linear_model import LinearRegression
# import scipy.ndimage
# from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
# from scipy.interpolate import griddata
import os
#-----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------CLASSES-----------------------------------------------------
from Phys_Math_Labels import Errors
from Phys_Math_Labels import Math
from Phys_Math_Labels import Physics
from Phys_Math_Labels import Constants
from Phys_Math_Labels import Labels

from OPAL import Read_Table
from OPAL import Row_Analyze
from OPAL import Table_Analyze
from OPAL import OPAL_Interpol
from OPAL import New_Table

from FilesWork import Read_Observables
from FilesWork import Read_Plot_file
from FilesWork import Read_SM_data_file
from FilesWork import Read_SP_data_file
from FilesWork import Save_Load_tables

from PhysPlots import PhysPlots
#-----------------------------------------------------------------------------------------------------------------------

class Combine:
    output_dir = '../data/output/'
    plot_dir = '../data/plots/'

    opal_used = ''
    sm_files = []
    sp_files = []

    obs_files =  ''
    plot_files = []
    m_l_relation = None

    def __init__(self):
        pass

    def set_files(self):
        self.mdl = []
        for file in self.sm_files:
            self.mdl.append( Read_SM_data_file.from_sm_data_file(file) )

        self.spmdl=[]
        for file in self.sp_files:
            self.spmdl.append( Read_SP_data_file(file, self.output_dir, self.plot_dir) )

        # self.nums = Num_Models(smfls, plotfls)
        self.obs = Read_Observables(self.obs_files, self.m_l_relation)

    # --- METHODS THAT DO NOT REQUIRE OPAL TABLES ---
    def xy_profile(self, v_n1, v_n2, var_for_label1, var_for_label2, sonic = True):

        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        tlt = v_n2 + '(' + v_n1 + ') profile'
        plt.title(tlt)

        for i in range(len(self.sm_files)):

            x =      self.mdl[i].get_col(v_n1)
            y      = self.mdl[i].get_col(v_n2)          # simpler syntaxis
            label1 = self.mdl[i].get_col(var_for_label1)[-1]
            label2 = self.mdl[i].get_col(var_for_label2)[-1]

            print('\t __Core H: {} , core He: {} File: {}'.
                  format(self.mdl[i].get_col('H')[0], self.mdl[i].get_col('He4')[0], self.sm_files[i]))

            lbl = '{}:{} , {}:{}'.format(var_for_label1,'%.2f' % label1,var_for_label2,'%.2f' % label2)
            ax1.plot(x,  y,  '-',   color='C' + str(Math.get_0_to_max([i], 9)[i]), label=lbl)
            ax1.plot(x, y, '.', color='C' + str(Math.get_0_to_max([i], 9)[i]), label=lbl)
            ax1.plot(x[-1], y[-1], 'x',   color='C' + str(Math.get_0_to_max([i], 9)[i]))

            ax1.annotate(str('%.2e' % 10**self.mdl[i].get_col('mdot')[-1]), xy=(x[-1], y[-1]), textcoords='data')


            if sonic and v_n2 == 'u':
                u_s = self.mdl[i].get_sonic_u()
                ax1.plot(x, u_s, '-', color='black')

                xc, yc = Math.interpolated_intercept(x,y, u_s)
                # print('Sonic r: {} | Sonic u: {} | {}'.format( np.float(xc),  np.float(yc), len(xc)))
                plt.plot(xc, yc, 'X', color='red', label='Intersection')

        ax1.set_xlabel(Labels.lbls(v_n1))
        ax1.set_ylabel(Labels.lbls(v_n2))

        ax1.grid(which='both')
        ax1.grid(which='minor', alpha=0.2)
        ax1.grid(which='major', alpha=0.2)

        ax1.legend(bbox_to_anchor=(0, 1), loc='upper left', ncol=1)
        plot_name = self.plot_dir + v_n1 + '_vs_' + v_n2 + '_profile.pdf'
        plt.savefig(plot_name)
        plt.show()

    def xyy_profile(self, v_n1, v_n2, v_n3, var_for_label1, var_for_label2, var_for_label3, edd_kappa = True):

        # for i in range(self.nmdls):
        #     x = self.mdl[i].get_col(v_n1)
        #     y = self.mdl[i].get_col(v_n2)
        #     color = 'C' + str(i)
        #
        #     lbl = 'M:' + str('%.2f' % self.mdl[i].get_col('xm')[-1]) + ' L:' + \
        #            str('%.2f' % self.mdl[i].get_col('l')[-1]) + ' Mdot:' + \
        #            str('%.2f' % self.mdl[i].get_col('mdot')[-1])
        #     ax1.plot(x, y, '-', color=color, label=lbl)
        #     ax1.plot(x[-1], y[-1], 'x', color=color)

        fig, ax1 = plt.subplots()
        tlt = v_n2 + ' , '+ v_n3 + ' = f(' + v_n1 + ') profile'
        plt.title(tlt)

        ax1.set_xlabel(v_n1)
        # Make the y-axis label, ticks and tick labels match the line color.
        ax1.set_ylabel(v_n2, color='b')
        ax1.tick_params('y', colors='b')
        ax1.grid()
        ax2 = ax1.twinx()

        for i in range(len(self.sm_files)):

            xyy2  = self.mdl[i].get_set_of_cols([v_n1, v_n2, v_n3])
            lbl1 =  self.mdl[i].get_col(var_for_label1)[-1]
            lbl2 =  self.mdl[i].get_col(var_for_label2)[-1]
            lbl3 =  self.mdl[i].get_col(var_for_label3)[-1]

            color = 'C' + str(Math.get_0_to_max([i], 9)[i])
            lbl = '{}:{} , {}:{} , {}:{}'.format(var_for_label1, '%.2f' % lbl1, var_for_label2, '%.2f' % lbl2,
                                                 var_for_label3, '%.2f' % lbl3)

            ax1.plot(xyy2[:, 0],  xyy2[:, 1],  '-', color=color, label=lbl)
            ax1.plot(xyy2[-1, 0], xyy2[-1, 1], 'x', color=color)
            ax1.annotate(str('%.2f' % lbl1), xy=(xyy2[-1, 0], xyy2[-1, 1]), textcoords='data')

            if edd_kappa and v_n3 == 'kappa':
                k_edd = Physics.edd_opacity(self.mdl[i].get_col('xm')[-1],
                                            self.mdl[i].get_col('l')[-1])
                ax2.plot(ax1.get_xlim(), [k_edd, k_edd], color='black', label='Model: {}, k_edd: {}'.format(i, k_edd))

            ax2.plot(xyy2[:, 0],  xyy2[:, 2], '--', color=color)
            ax2.plot(xyy2[-1, 0], xyy2[-1, 2], 'o', color=color)

        ax2.set_ylabel(v_n3, color='r')
        ax2.tick_params('y', colors='r')

        plt.title(tlt, loc='left')
        fig.tight_layout()
        ax1.legend(bbox_to_anchor=(0, 1), loc='upper left', ncol=1)
        plot_name = self.plot_dir + v_n1 + '_' + v_n2 + '_' + v_n3 + '_profile.pdf'
        plt.savefig(plot_name)
        plt.show()

    def hrd(self, l_or_lm):

        fig, ax = plt.subplots(1, 1)

        plt.title('HRD')
        plt.xlabel(Labels.lbls('t_eff'))
        plt.ylabel(Labels.lbls(l_or_lm))

        # plt.xlim(t1, t2)
        ax.grid(which='major', alpha=0.2)
        plt.legend(bbox_to_anchor=(1, 1), loc='upper right', ncol=1)

        # res = self.obs.get_x_y_of_all_observables('t', 'l', 'type')
        #
        # for i in range(len(res[0][:, 1])):
        #     ax.annotate(int(res[0][i, 0]), xy=(res[0][i, 1], res[0][i, 2]), textcoords='data')  # plot numbers of stars
        #     plt.plot(res[0][i, 1], res[0][i, 2], marker='^', color='C' + str(int(res[0][i, 3])),
        #              ls='')  # plot color dots)))
        #
        # for j in range(len(res[1][:, 0])):
        #     plt.plot(res[1][j, 1], res[1][j, 2], marker='^', color='C' + str(int(res[1][j, 3])), ls='',
        #              label='WN' + str(int(res[1][j, 3])))

        ind_arr = []
        for j in range(len(self.plot_files)):
            ind_arr.append(j)
            col_num = Math.get_0_to_max(ind_arr, 9)
            plfl = Read_Plot_file.from_file(self.plot_files[j])

            mod_x = plfl.t_eff
            if l_or_lm == 'l':
                mod_y = plfl.l_
            else:
                mod_y = plfl.l_/plfl.m_


            color = 'C' + str(col_num[j])

            fname = self.plot_files[j].split('/')[-2] + self.plot_files[j].split('/')[-1]# get the last folder in which the .plot1 is

            plt.plot(mod_x, mod_y, '-', color=color, label = '{}'.format("%.1f" % plfl.m_[0])+' M$_{\odot}$' )
                     # label='{}, m:({}->{})'.format(fname, "%.1f" % plfl.m_[0], "%.1f" % plfl.m_[-1]) )
                     # str("%.2f" % plfl.m_[0]) + ' to ' + str("%.2f" % plfl.m_[-1]) + ' solar mass')


            imx = Math.find_nearest_index( plfl.y_c, plfl.y_c.max() )
            plt.plot(mod_x[imx], mod_y[imx], 'x')
            ax.annotate("%.4f" % plfl.y_c.max(), xy=(mod_x[imx], mod_y[imx]), textcoords='data')

            plt.plot()

            for i in range(10):
                ind = Math.find_nearest_index(plfl.y_c, (i / 10))
                # print(plfl.y_c[i], (i/10))
                x_p = mod_x[ind]
                y_p = mod_y[ind]
                plt.plot(x_p, y_p, '.', color='red')
                ax.annotate("%.2f" % plfl.y_c[ind], xy=(x_p, y_p), textcoords='data')

        ax.grid(which='both')
        ax.grid(which='minor', alpha=0.2)

        plt.gca().invert_xaxis() # inverse x axis

        plt.grid()

        plt.legend(bbox_to_anchor=(0, 0), loc='lower left', ncol=1)
        plot_name = self.output_dir + 'hrd.pdf'
        plt.savefig(plot_name)

        plt.show()

    def xy_last_points(self, v_n1, v_n2, v_lbl1, num_pol_fit = True):
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)

        # nums = Treat_Numercials(self.num_files)  # Surface Temp as a x coordinate
        # res = nums.get_x_y_of_all_numericals('sp', 'r', 'l', 'mdot', 'color')
        x = []
        y = []
        for i in range(len(self.sm_files)):
            x = np.append(x, self.mdl[i].get_cond_value(v_n1, 'sp') )
            y = np.append(y, self.mdl[i].get_cond_value(v_n2, 'sp') )

            lbl1 = self.mdl[i].get_cond_value(v_lbl1, 'sp')
            # print(x, y, lbl1)

            plt.plot(x[i], y[i], marker='.', color='C' + str(Math.get_0_to_max([i],9)[i]), ls='', label='{}:{} , {}:{} , {}:{}'
                     .format(v_n1, "%.2f" % x[i], v_n2, "%.2f" % y[i], v_lbl1, "%.2f" % lbl1))  # plot color dots)))
            ax.annotate(str("%.2f" % lbl1), xy=(x[i], y[i]), textcoords='data')

        if num_pol_fit:
            fit = np.polyfit(x, y, 3)  # fit = set of coeddicients (highest first)
            f = np.poly1d(fit)

            # print('Equation:', f.coefficients)
            fit_x_coord = np.mgrid[(x.min()):(x.max()):100j]
            plt.plot(fit_x_coord, f(fit_x_coord), '--', color='black', label='Model_fit')


        name = self.output_dir+'{}_{}_dependance.pdf'.format(v_n2,v_n1)
        plt.title('{} = f({}) plot'.format(v_n2,v_n1))
        plt.xlabel(Labels.lbls(v_n1))
        plt.ylabel(Labels.lbls(v_n2))
        plt.legend(bbox_to_anchor=(0, 0), loc='lower left', ncol=1)
        plt.savefig(name)

        plt.show()

    def sp_xy_last_points(self, v_n1, v_n2, v_lbl1, num_pol_fit = 0):

        def fit_plynomial(x, y, order):
            '''

            :param x:
            :param y:
            :param order: 1-4 are supported
            :return:
            '''
            f = None
            fit_x_coord = []

            if order == 1:
                fit = np.polyfit(x, y, order)  # fit = set of coeddicients (highest first)
                f = np.poly1d(fit)
                lbl = '({}) + ({}*x)'.format(
                    "%.3f" % f.coefficients[1],
                    "%.3f" % f.coefficients[0]
                )
                fit_x_coord = np.mgrid[(x.min()):(x.max()):100j]
                plt.plot(fit_x_coord, f(fit_x_coord), '--', color='black')

            if order == 2:
                fit = np.polyfit(x, y, order)  # fit = set of coeddicients (highest first)
                f = np.poly1d(fit)
                lbl = '({}) + ({}*x) + ({}*x**2)'.format(
                                                                    "%.3f" % f.coefficients[2],
                                                                    "%.3f" % f.coefficients[1],
                                                                    "%.3f" % f.coefficients[0]
                                                                    )
                fit_x_coord = np.mgrid[(x.min()):(x.max()):100j]
                plt.plot(fit_x_coord, f(fit_x_coord), '--', color='black')
            if order == 3:
                fit = np.polyfit(x, y, order)  # fit = set of coeddicients (highest first)
                f = np.poly1d(fit)
                lbl = '({}) + ({}*x) + ({}*x**2) + ({}*x**3)'.format(
                                                                    "%.3f" % f.coefficients[3],
                                                                    "%.3f" % f.coefficients[2],
                                                                    "%.3f" % f.coefficients[1],
                                                                    "%.3f" % f.coefficients[0]
                                                                    )
                fit_x_coord = np.mgrid[(x.min()):(x.max()):100j]
                plt.plot(fit_x_coord, f(fit_x_coord), '--', color='black')
            if order == 4:
                fit = np.polyfit(x, y, order)  # fit = set of coeddicients (highest first)
                f = np.poly1d(fit)
                lbl = '({}) + ({}*x) + ({}*x**2) + ({}*x**3) + ({}*x**4)'.format(
                                                                     "%.3f" % f.coefficients[4],
                                                                    "%.3f" % f.coefficients[3],
                                                                    "%.3f" % f.coefficients[2],
                                                                    "%.3f" % f.coefficients[1],
                                                                    "%.3f" % f.coefficients[0]
                                                                    )
                fit_x_coord = np.mgrid[(x.min()):(x.max()):100j]
                plt.plot(fit_x_coord, f(fit_x_coord), '--', color='black')

            print(lbl)

            return fit_x_coord, f(fit_x_coord)

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)

        # nums = Treat_Numercials(self.num_files)  # Surface Temp as a x coordinate
        # res = nums.get_x_y_of_all_numericals('sp', 'r', 'l', 'mdot', 'color')
        x = []
        y = []
        yc =[]
        xm = []
        for i in range(len(self.sp_files)):

            x = np.append(x, self.spmdl[i].get_crit_value(v_n1) )
            y = np.append(y, self.spmdl[i].get_crit_value(v_n2) )
            yc = np.append(yc, self.spmdl[i].get_crit_value('Yc'))
            xm = np.append(xm, self.spmdl[i].get_crit_value('m'))

            lbl1 = self.spmdl[i].get_crit_value(v_lbl1)

            # print(x, y, lbl1) label='{} | {}:{} , {}:{} , {}:{}, Yc: {}'
            #          .format(i, v_n1, "%.2f" % x[i], v_n2, "%.2f" % y[i], v_lbl1, "%.2f" % lbl1, yc[i])

            plt.plot(x[i], y[i], marker='.', color='black', ls='', label=lbl1)  # plot color dots)))
            ax.annotate(str("%.2f" % xm[i]), xy=(x[i], y[i]), textcoords='data')

            # "%.2f" % yc[i]

        x_pol, y_pol = fit_plynomial(x, y, num_pol_fit)

        plt.plot(x_pol, y_pol, '--', color='black')

        if v_n1 == 'm' and v_n2 == 'l':
            plt.plot(x, Physics.m_to_l(np.log10(x)), '-.', color='gray', label='Langer, 1987')


        # plt.plot(x, y, '-', color='gray')


        name = self.output_dir+'{}_{}_dependance.pdf'.format(v_n2,v_n1)
        plt.title('{} = f({}) plot'.format(v_n2, v_n1))
        plt.xlabel(Labels.lbls(v_n1))
        plt.ylabel(Labels.lbls(v_n2))
        plt.legend(bbox_to_anchor=(1, 0), loc='lower right', ncol=1)
        plt.savefig(name)
        plt.grid()

        plt.show()

    # --- METHODS THAT DO REQUIRE OPAL TABLES ---
    def sp_get_r_lt_table2(self, v_n, l_or_lm, plot=True, ref_t_llm_vrho=np.empty([])):
        '''

        :param l_or_lm:
        :param depth:
        :param plot:
        :param t_llm_vrho:
        :return:
        '''
        if not ref_t_llm_vrho.any():
            print('\t__ No *ref_t_llm_vrho* is provided. Loading {} interp. opacity table.'.format(self.opal_used))
            t_k_rho = Save_Load_tables.load_table('t_k_rho', 't', 'k', 'rho', self.opal_used, self.output_dir)
            table = Physics.t_kap_rho_to_t_llm_rho(t_k_rho, l_or_lm)
        else:
            table = ref_t_llm_vrho

        t_ref = table[0, 1:]
        llm_ref=table[1:, 0]
        # rho_ref=table[1:, 1:]


        '''=======================================ESTABLISHING=LIMITS================================================'''

        t_mins = []
        t_maxs = []

        for i in range(len(self.sp_files)): # as every sp.file has different number of t - do it one by one

            t = self.spmdl[i].get_sonic_cols('t')                     # Sonic
            t = np.append(t, self.spmdl[i].get_crit_value('t'))       # critical

            t_mins = np.append(t_mins, t.min())
            t_maxs = np.append(t_maxs, t.max())

        t_min = t_mins.max()
        t_max = t_maxs.min()

        print('\t__ SP files t limits: ({}, {})'.format(t_min, t_max))
        print('\t__REF table t limits: ({}, {})'.format(t_ref.min(), t_ref.max()))

        it1 = Math.find_nearest_index(t_ref, t_min)       # Lower t limit index in t_ref
        it2 = Math.find_nearest_index(t_ref, t_max)       # Upper t limit index in t_ref
        t_grid = t_ref[it1:it2]

        print('\t__     Final t limits: ({}, {}) with {} elements'.format(t_ref[it1], t_ref[it2], len(t_grid)))


        '''=========================INTERPOLATING=ALONG=T=ROW=TO=HAVE=EQUAL=N=OF=ENTRIES============================='''

        llm_r_rows = np.empty(1 + len(t_ref[it1:it2]))

        for i in range(len(self.sp_files)):

            if l_or_lm == 'l':
                llm = self.spmdl[i].get_crit_value('l')
            else:
                llm = Physics.loglm(self.spmdl[i].get_crit_value('l'), self.spmdl[i].get_crit_value('m'), False)


            r = self.spmdl[i].get_sonic_cols(v_n)                     # get sonic
            if v_n == 'r': r = np.append(r, self.spmdl[i].get_crit_value('r'))       # get Critical

            t = self.spmdl[i].get_sonic_cols('t')                                     # Sonic
            if v_n == 'r': t = np.append(t, self.spmdl[i].get_crit_value('t'))        # critical

            r_t = []        # Dictionary for sorting
            for i in range(len(r)):
                r_t = np.append(r_t, [r[i], t[i]])

            r_t_sort = np.sort(r_t.view('float64, float64'), order=['f1'], axis=0).view(np.float)
            r_t_reshaped = np.reshape(r_t_sort, (len(r), 2)) # insure that the t values are rising along the t_r arr.

            r_sort = r_t_reshaped[:,0]
            t_sort = r_t_reshaped[:,1]

            f = interpolate.InterpolatedUnivariateSpline(t_sort, r_sort)

            l_r_row = np.array([llm])
            l_r_row = np.append(l_r_row, f(t_grid))
            llm_r_rows = np.vstack((llm_r_rows, l_r_row))

        llm_r_rows = np.delete(llm_r_rows, 0, 0)

        llm_r_rows_sort = llm_r_rows[llm_r_rows[:,0].argsort()] # UNTESTED sorting function

        t_llm_r = Math.combine(t_grid, llm_r_rows_sort[:,0], llm_r_rows_sort[:,1:]) # intermediate result

        '''======================================INTERPOLATING=EVERY=COLUMN=========================================='''


        l      = t_llm_r[1:, 0]
        t      = t_llm_r[0, 1:]
        r      = t_llm_r[1:, 1:]
        il1    = Math.find_nearest_index(llm_ref, l.min())
        il2    = Math.find_nearest_index(llm_ref, l.max())

        print('\t__ SP files l limits: ({}, {})'.format(l.min(), l.max()))
        print('\t__REF table t limits: ({}, {})'.format(llm_ref.min(), llm_ref.max()))

        l_grid = llm_ref[il1:il2]

        print('\t__     Final l limits: ({}, {}) with {} elements'.format(llm_ref[il1], llm_ref[il2], len(l_grid)))

        r_final = np.empty((len(l_grid),len(t)))
        for i in range(len(t)):
            f = interpolate.InterpolatedUnivariateSpline(l, r[:, i])
            r_final[:, i] = f(l_grid)

        t_llm_r = Math.combine(t, l_grid, r_final)

        if plot:
            plt.figure()
            # ax = fig.add_subplot(1, 1, 1)
            plt.xlim(t_llm_r[0,1:].min(), t_llm_r[0,1:].max())
            plt.ylim(t_llm_r[1:,0].min(), t_llm_r[1:,0].max())
            plt.ylabel(Labels.lbls(l_or_lm))
            plt.xlabel(Labels.lbls('ts'))

            levels = []
            if v_n == 'k':   levels = [0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95] # FOR log Kappa
            if v_n == 'rho': levels = [-10, -9.5, -9, -8.5, -8, -7.5, -7, -6.5, -6, -5.5,  -5, -4.5, -4]
            if v_n == 'r':   levels = [0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5, 1.55, 1.6, 1.65, 1.7,
                                       1.75, 1.8, 1.85, 1.9, 1.95, 2.0, 2.05, 2.10, 2.15, 2.20]

            contour_filled = plt.contourf(t_llm_r[0, 1:], t_llm_r[1:, 0], t_llm_r[1:,1:], levels, cmap=plt.get_cmap('RdYlBu_r'))
            plt.colorbar(contour_filled, label=Labels.lbls(v_n))
            contour = plt.contour(t_llm_r[0, 1:], t_llm_r[1:, 0], t_llm_r[1:,1:], levels, colors='k')
            plt.clabel(contour, colors='k', fmt='%2.2f', fontsize=12)
            plt.title('SONIC HR DIAGRAM')

            # plt.ylabel(l_or_lm)
            plt.legend(bbox_to_anchor=(0, 0), loc='lower left', ncol=1)
            # plt.savefig(name)
            plt.show()

        return t_llm_r

    def sp_get_r_lt_table(self, l_or_lm, depth = 1000, plot = False, t_llm_vrho = np.empty([])):
        '''

        :param l_or_lm:
        :param t_grid:
        :param l_lm:
        :t_llm_vrho:
        :return:
        '''
        '''===========================INTERPOLATING=EVERY=ROW=TO=HAVE=EQUAL=N=OF=ENTRIES============================='''

        r = np.empty((len(self.sp_files), 100))
        t = np.empty((len(self.sp_files), 100))
        l_lm = np.empty(len(self.sp_files))

        for i in range(len(self.sp_files)):
            r_i =  self.spmdl[i].get_sonic_cols('r')
            r_i = np.append(r_i, self.spmdl[i].get_crit_value('r'))

            t_i = self.spmdl[i].get_sonic_cols('t')
            t_i = np.append(t_i, self.spmdl[i].get_crit_value('t'))

            r_i_grid = np.mgrid[r_i.min():r_i.max():100j]
            f = interpolate.InterpolatedUnivariateSpline(r_i, t_i)
            t_i_grid = f(r_i_grid)

            r[i,:] = r_i_grid
            t[i,:] = t_i_grid

            if l_or_lm == 'l':
                l_lm[i] = self.spmdl[i].get_crit_value('l')
            else:
                l_lm[i] = Physics.loglm(self.spmdl[i].get_crit_value('l'), self.spmdl[i].get_crit_value('m'), False)

        '''====================================CREATING=OR=USING=L/T=GRID============================================'''

        if t_llm_vrho.any():

            t__ =  t_llm_vrho[0,1:]
            l_lm_grid_ = t_llm_vrho[1:, 0]
            vrho = t_llm_vrho[1:,1:]

            if l_lm_grid_[0] > l_lm_grid_[-1]:
                raise ValueError('Array l_lm_grid_ must be increasing, now it is from {} to {}'
                                 .format(l_lm_grid_[0], l_lm_grid_[-1]))


            l_lm_1 = l_lm.min()
            i1 = Math.find_nearest_index(l_lm_grid_, l_lm_1)
            l_lm_2 = l_lm.max()
            i2 = Math.find_nearest_index(l_lm_grid_, l_lm_2)

            l_lm_grid = l_lm_grid_[i1:i2]
            vrho = vrho[i1:i2,:]

            t_llm_vrho = Math.combine(t__, l_lm_grid, vrho)

            print('\t__Note: provided l_lm_grid_{} is cropped to {}, with limits: ({}, {})'
                  .format(l_lm_grid_.shape, l_lm_grid.shape, l_lm_grid.min(), l_lm_grid.max()))

        else:
            l_lm_grid = np.mgrid[l_lm.min():l_lm.max():depth*1j]

        '''=======================================INTERPOLATE=2D=T=AND=R============================================='''

        r2 = np.empty(( len(l_lm_grid), len(r[0,:]) ))
        t2 = np.empty(( len(l_lm_grid), len(r[0,:]) ))

        for i in range( len(r[0, :]) ):

            r_l = [] # DICTIONARY
            for j in range(len(r[:,i])): # this wierd thing allows you to create a dictionary that you can sort
               r_l = np.append(r_l, [ r[j,i], l_lm[j] ])

            r_l_  = np.sort(r_l.view('f8, f8'), order=['f1'], axis=0).view(np.float) # sorting dictionary according to l_lm
            r_l__ = np.reshape(r_l_, (len(l_lm), 2))


            r_ = r_l__[:,0] # i-th column, sorted by l_lm
            l_lm_ = r_l__[:,1] # l_lm sorted

            f2 = interpolate.InterpolatedUnivariateSpline(l_lm_, r_) # column by column it goes
            r2[:,i] = f2(l_lm_grid)


            # --- --- --- T --- --- ---

        for i in range( len(t[0, :]) ):
            t_l_lm = [] # DICTIONARY
            for j in range(len(t[:,i])): # this wierd thing allows you to create a dictionary that you can sort
               t_l_lm = np.append(t_l_lm, [ t[j,i], l_lm[j] ])

            t_l_lm_  = np.sort(t_l_lm.view('f8, f8'), order=['f1'], axis=0).view(np.float) # sorting dictionary according to l_lm
            t_l_lm__ = np.reshape(t_l_lm_, (len(l_lm), 2))


            t_ = t_l_lm__[:,0] # i-th column, sorted by l_lm
            l_lm_ = t_l_lm__[:,1] # l_lm sorted

            f2 = interpolate.InterpolatedUnivariateSpline(l_lm_, t_) # column by column it goes

            # if l_lm_grid.min() < l_lm_.min() or l_lm_grid.max() > l_lm_.max():
            #     raise ValueError('l_lm_grid.min({}) < l_lm_.min({}) or l_lm_grid.max({}) > l_lm_.max({})'
            #                      .format(l_lm_grid.min() , l_lm_.min() , l_lm_grid.max() , l_lm_.max()))

            t2[:,i] = f2(l_lm_grid)


        '''=======================================INTERPOLATE=R=f(L, T)=============================================='''

        # If in every row of const. l_lm, the temp 't' is decreasing monotonically:
        t2_ = t2[:, ::-1]    # so t is from min to max increasing
        r2_ = r2[:, ::-1]    # necessary of Univariate spline

        if not t2_.any() or not r2_.any():
            raise ValueError('Array t2_{} or r2_{} is empty'.format(t2_.shape, r2_.shape))

        def interp_t_l_r(l_1d_arr, t_2d_arr, r_2d_arr, depth = 1000, t_llm_vrho = np.empty([])):

            t1 = t_2d_arr[:, 0].max()
            t2 = t_2d_arr[:,-1].min()



            '''------------------------SETTING-T-GRID-OR-CROPPING-THE-GIVEN-ONE--------------------------------------'''
            if t_llm_vrho.any():

                t_grid_ = t_llm_vrho[0, 1:]
                l_lm_grid_ = t_llm_vrho[1:, 0]
                vrho = t_llm_vrho[1:, 1:]

                if t_grid_[0] > t_grid_[-1]:
                    raise ValueError('Array t_grid_ must be increasing, now it is from {} to {}'
                                     .format(t_grid_[0], t_grid_[-1]))

                i1 = Math.find_nearest_index(t_grid_, t1)
                i2 = Math.find_nearest_index(t_grid_, t2)

                print('\t  t1:{}[i:{}] t2:{}[i:{}] '.format(t1,i1,t2,i2))

                crop_t_grid = t_grid_[i1:i2]
                vrho = vrho[:,i1:i2]

                t_llm_vrho = Math.combine(crop_t_grid, l_lm_grid_, vrho)


                print('\t__Note: provided t_grid{} is cropped to {}, with limits: ({}, {})'
                      .format(t_grid_.shape, crop_t_grid.shape, crop_t_grid.min(), crop_t_grid.max()))
            else:
                crop_t_grid = np.mgrid[t1:t2:depth * 1j]
                t_llm_vrho = np.empty([])

            '''---------------------USING-2*1D-INTERPOLATIONS-TO-GO-FROM-2D_T->1D_T----------------------------------'''


            crop_r = np.empty(( len(l_1d_arr), len(crop_t_grid) ))
            crop_l_lm = []

            for si in range(len(l_1d_arr)):
                # if t1 <= t_2d_arr[si, :].max() and t2 >= t_2d_arr[si, :].min():

                t_row = t_2d_arr[si, :]
                r_row = r_2d_arr[si, :]

                print(t_row.shape, r_row.shape, crop_t_grid.T.shape)

                crop_r[si, :] = Math.interp_row(t_row, r_row, crop_t_grid.T)
                crop_l_lm = np.append(crop_l_lm, l_1d_arr[si])


            extend_crop_l = l_1d_arr # np.mgrid[l_1d_arr.min():l_1d_arr.max():depth*1j]

            extend_r = np.zeros((len(extend_crop_l), len(crop_t_grid)))

            print(crop_l_lm.shape, crop_r.shape, extend_crop_l.shape)

            for si in range(len(extend_r[0,:])):
                extend_r[:,si] = Math.interp_row( crop_l_lm, crop_r[:, si], extend_crop_l )

            return Math.combine(crop_t_grid, extend_crop_l, extend_r), t_llm_vrho

        t_l_or_lm_r, t_llm_vrho = interp_t_l_r(l_lm_grid, t2_, r2_, 1000, t_llm_vrho)

        if plot:
            plt.figure()
            # ax = fig.add_subplot(1, 1, 1)
            plt.xlim(t_l_or_lm_r[0,1:].min(), t_l_or_lm_r[0,1:].max())
            plt.ylim(t_l_or_lm_r[1:,0].min(), t_l_or_lm_r[1:,0].max())
            plt.ylabel(Labels.lbls(l_or_lm))
            plt.xlabel(Labels.lbls('ts'))
            levels = [0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5, 1.55, 1.6, 1.65, 1.7, 1.75, 1.8]
            contour_filled = plt.contourf(t_l_or_lm_r[0, 1:], t_l_or_lm_r[1:, 0], t_l_or_lm_r[1:,1:], levels, cmap=plt.get_cmap('RdYlBu_r'))
            plt.colorbar(contour_filled, label=Labels.lbls('r'))
            contour = plt.contour(t_l_or_lm_r[0, 1:], t_l_or_lm_r[1:, 0], t_l_or_lm_r[1:,1:], levels, colors='k')
            plt.clabel(contour, colors='k', fmt='%2.2f', fontsize=12)
            plt.title('SONIC HR DIAGRAM')

            # plt.ylabel(l_or_lm)
            plt.legend(bbox_to_anchor=(0, 0), loc='lower left', ncol=1)
            # plt.savefig(name)
            plt.show()

        return t_l_or_lm_r, t_llm_vrho

    def plot_t_rho_kappa(self, var_for_label1, var_for_label2,  n_int_edd = 1000, plot_edd = True):
        # self.int_edd = self.tbl_anlom_OPAL_table(self.op_name, 1, n_int, load_lim_cases)

        # t_k_rho = self.opal.interp_opal_table(t1, t2, rho1, rho2)

        t_rho_k = Save_Load_tables.load_table('t_rho_k','t','rho','k',self.opal_used, self.output_dir)


        t      = t_rho_k[0, 1:]  # x
        rho    = t_rho_k[1:, 0]  # y
        kappa  = t_rho_k[1:, 1:] # z

        plt.figure()
        levels = [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
        pl.xlim(t.min(), t.max())
        pl.ylim(rho.min(), rho.max())
        contour_filled = plt.contourf(t, rho, 10 ** (kappa), levels, cmap=plt.get_cmap('RdYlBu_r'))
        plt.colorbar(contour_filled)
        contour = plt.contour(t, rho, 10 ** (kappa), levels, colors='k')
        plt.clabel(contour, colors='k', fmt='%2.1f', fontsize=12)
        plt.title('OPACITY PLOT')
        plt.xlabel('Log(T)')
        plt.ylabel('log(rho)')

        # ------------------------EDDINGTON-----------------------------------
        Table_Analyze.plot_k_vs_t = False  # there is no need to plot just one kappa in the range of availability

        if plot_edd:  # n_model_for_edd_k.any():
            clas_table_anal = Table_Analyze(self.opal_used, 1000, False, self.output_dir, self.plot_dir)

            for i in range(len(self.sm_files)):  # self.nmdls
                mdl_m = self.mdl[i].get_value('xm', 'sp')
                mdl_l = self.mdl[i].get_value('l',  'sp')

                k_edd = Physics.edd_opacity(mdl_m, mdl_l)

                n_model_for_edd_k = clas_table_anal.interp_for_single_k(t.min(), t.max(), n_int_edd, k_edd)
                x = n_model_for_edd_k[0, :]
                y = n_model_for_edd_k[1, :]
                color = 'black'
                lbl = 'Model:{}, k_edd:{}'.format(i, '%.2f' % 10 ** k_edd)
                plt.plot(x, y, '-.', color=color, label=lbl)
                plt.plot(x[-1], y[-1], 'x', color=color)

        Table_Analyze.plot_k_vs_t = True
        # ----------------------DENSITY----------------------------------------

        for i in range(len(self.sm_files)):
            res = self.mdl[i].get_set_of_cols(['t', 'rho', var_for_label1, var_for_label2])

            lbl = '{} , {}:{} , {}:{}'.format(i, var_for_label1, '%.2f' % res[0, 2], var_for_label2, '%.2f' % res[0, 3])
            plt.plot(res[:, 0], res[:, 1], '-', color='C' + str(Math.get_0_to_max([i], 9)[i]), label=lbl)
            plt.plot(res[-1, 0], res[-1, 1], 'x', color='C' + str(Math.get_0_to_max([i], 9)[i]))
            plt.annotate(str('%.2f' % res[0, 2]), xy=(res[-1, 0], res[-1, 1]), textcoords='data')

        plt.legend(bbox_to_anchor=(0, 0), loc='lower left', ncol=1)
        name = self.plot_dir + 't_rho_kappa.pdf'
        plt.savefig(name)
        plt.show()

    def plot_t_mdot_lm(self, v_lbl, r_s = 1., lim_t1_mdl = 5.2, lim_t2_mdl = None):

        t_rho_k = Save_Load_tables.load_table('t_rho_k', 't', 'rho', 'k', self.opal_used,self.output_dir)

        t_s= t_rho_k[0, 1:]  # x
        rho= t_rho_k[1:, 0]  # y
        k  = t_rho_k[1:, 1:]  # z

        vrho = Physics.get_vrho(t_s, rho, 1, 1.34)    # assuming mu = constant
        mdot = Physics.vrho_mdot(vrho, r_s, '')       # assuming rs = constant

        lm_arr = Physics.logk_loglm(k, 2)

        #-----------------------------------

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        pl.xlim(t_s.min(), t_s.max())
        pl.ylim(mdot.min(), mdot.max())
        levels = [3.0, 3.2, 3.4, 3.6, 3.8, 4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.0, 5.2]
        contour_filled = plt.contourf(t_s, mdot, lm_arr, levels, cmap=plt.get_cmap('RdYlBu_r'))
        plt.colorbar(contour_filled)
        contour = plt.contour(t_s, mdot, lm_arr, levels, colors='k')
        plt.clabel(contour, colors='k', fmt='%2.1f', fontsize=12)
        plt.title('L/M PLOT')
        plt.xlabel('Log(t_s)')
        plt.ylabel('log(M_dot)')

        for i in range(len(self.sm_files)):
            ts_llm_mdot = self.mdl[i].get_xyz_from_yz(i, 'sp', 'mdot', 'lm', t_s,mdot, lm_arr, lim_t1_mdl, lim_t2_mdl)
            lbl1 = self.mdl[i].get_cond_val(v_lbl, 'sp')

            if ts_llm_mdot.any():
                lbl = 'i:{}, lm:{}, {}:{}'.format(i, "%.2f" % ts_llm_mdot[2, -1], v_lbl, "%.2f" % lbl1)
                plt.plot(ts_llm_mdot[0, :], ts_llm_mdot[1,:], marker='x', color='C' + str(Math.get_0_to_max([i],9)[i]), ls='', label=lbl)  # plot color dots)))
                ax.annotate(str("%.2f" % ts_llm_mdot[2, -1]), xy=(ts_llm_mdot[0, -1], ts_llm_mdot[1,-1]), textcoords='data')

        plt.legend(bbox_to_anchor=(1, 0), loc='lower right', ncol=1)
        name = self.plot_dir + 't_mdot_lm_plot.pdf'
        plt.savefig(name)
        plt.show()

    @staticmethod
    def llm_r_formulas(x, yc, z, l_or_lm):

        def crop_x(x, lim_arr):
            if len(lim_arr) > 1:
                raise ValueError('Size of a lim_arr must be 2 [min, max], but provided {}'.format(lim_arr))
            return x[Math.find_nearest_index(x, lim_arr[0]) : Math.find_nearest_index(x, lim_arr[-1])]

        #=======================================EMPIRICAL=FUNCTIONS=AND=LIMITS==========================================
        if z == 0.02 or z == 'gal':
            if yc == 1. or yc == 10 or yc == 'zams':
                if l_or_lm == 'l':
                    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --
                    l_lim = []    # put here the l limits for which the polynomial fit is accurate
                    x = crop_x(x, l_lim)
                    return None # Put here the polinomoal (x-l, y-r)
                    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --
                else:
                    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --
                    lm_lim= []
                    x = crop_x(x, lm_lim)
                    return None
                    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --

        if z == 0.008 or z == 'lmc':
            if yc == 1. or yc == 10 or yc == 'zams':
                if l_or_lm == 'l':
                    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --
                    l_lim = []    # put here the l limits for which the polynomial fit is accurate
                    x = crop_x(x, l_lim)
                    return None # Put here the polinomoal (x-l, y-r)
                    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --
                else:
                    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --
                    lm_lim= []
                    x = crop_x(x, lm_lim)
                    return None
                    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --

        #====================================================END========================================================

    def empirical_l_r_crit(self, t_k_rho, l_or_lm):
        '''
        READS the SP files for r_crit and l/lm. Than depending on limits of l/lm in SP and limits in OPAL
        selects the availabel range of l/am and uses OPAL values of l/lm as a grid, to interpolate critical R values
        :param t_k_rho:
        :param l_or_lm:
        :param yc:
        :param z:
        :return:
        '''

        kap = t_k_rho[1:, 0]
        t   = t_k_rho[0, 1:]
        rho2d = t_k_rho[1:, 1:]

        l_lm_r = []

        for i in range(len(self.sp_files)):
            l    = self.spmdl[i].get_crit_value('l')
            m    = self.spmdl[i].get_crit_value('m')
            lm   = Physics.loglm(l, m, False)
            r_cr = self.spmdl[i].get_crit_value('r')
            # t_cr = self.spmdl[i].get_crit_value('t')

            l_lm_r = np.append(l_lm_r, [l, lm, r_cr])

        if l_or_lm == 'l':
            l_lm_r_sorted = np.sort(l_lm_r.view('f8, f8, f8'), order=['f0'], axis=0).view(np.float)
            l_lm_r_shaped = np.reshape(l_lm_r_sorted, (len(self.sp_files), 3))
            l_lm_emp = l_lm_r_shaped[:,0]
            r_cr_emp = l_lm_r_shaped[:,2]

            l_lm_opal = Physics.lm_to_l(Physics.logk_loglm(kap, True))
            t_llm_rhp_inv = Math.invet_to_ascending_xy(Math.combine(t, l_lm_opal, rho2d))
        else:
            l_lm_r_sorted = np.sort(l_lm_r.view('f8, f8, f8'), order=['f1'], axis=0).view(np.float)
            l_lm_r_shaped = np.reshape(l_lm_r_sorted, (len(self.sp_files), 3))
            l_lm_emp = l_lm_r_shaped[:,1]
            r_cr_emp = l_lm_r_shaped[:,2]

            l_lm_opal = Physics.logk_loglm(kap, True)
            t_llm_rhp_inv = Math.invet_to_ascending_xy(Math.combine(t, l_lm_opal, rho2d))


        l_lim1 = np.array([l_lm_emp.min(), l_lm_opal.min()]).max()
        l_lim2 = np.array([l_lm_emp.max(), l_lm_opal.max()]).min()

        print('\t__Note: Opal <{}> limits: ({}, {}) | SP files <{}> limits: ({}, {}) \n\t  Selected: ({}, {})'
              .format(l_or_lm, "%.2f" % l_lm_opal.min(), "%.2f" %  l_lm_opal.max(),
                      l_or_lm, "%.2f" %  l_lm_emp.min(), "%.2f" %  l_lm_emp.max(),
                      "%.2f" %  l_lim1, "%.2f" % l_lim2))


        cropped = Math.crop_2d_table(t_llm_rhp_inv, None, None, l_lim1, l_lim2)
        l_lm  = cropped[1:, 0]
        t     = cropped[0, 1:]
        rho2d = cropped[1:,1:]

        f = interpolate.UnivariateSpline(l_lm_emp, r_cr_emp)
        r_arr = f(l_lm)

        vrho = Physics.get_vrho(t, rho2d, 2, np.array([1.34]))
        m_dot = Physics.vrho_mdot(vrho, r_arr, 'l')

        return Math.combine(t, l_lm, m_dot)

        # else:
        #     l_lm_table = Physics.lm_to_l(Physics.logk_loglm(kap, True))
        #     l_lm_r_sorted = np.sort(l_lm_r.view('f8, f8'), order=['f1'], axis=0).view(np.float)
        #     l_lm_r_shaped = np.reshape(l_lm_r_sorted, (len(self.sp_files), 3))
        #
        #
        #
        #
        #
        #
        # if l_or_lm == 'l':  # to account for different limits in mass and luminocity
        #     l = Physics.lm_to_l( Physics.logk_loglm(kap, True) )
        #     cropped = Math.crop_2d_table(Math.invet_to_ascending_xy(Math.combine(t, l, rho2d)),
        #                                  None, None, l_lim[0], l_lim[-1])
        #
        #     l_lm = cropped[1:, 0]
        #     t = cropped[0, 1:]
        #     rho2d = cropped[1:, 1:]
        #
        #     vrho = Physics.get_vrho(t, rho2d, 2)
        #     m_dot = Physics.vrho_mdot(vrho, Combine.llm_r_formulas(l_lm, yc, z, l_or_lm), 'l')  # r_s = given by the func
        #
        # else:
        #     lm = Physics.logk_loglm(kap, True)
        #     cropped = Math.crop_2d_table(Math.invet_to_ascending_xy(Math.combine(t, lm, rho2d)),
        #                                  None, None, lm_lim[0], lm_lim[-1])
        #
        #
        #     l_lm = cropped[1:, 0]
        #     t    = cropped[0, 1:]
        #     rho2d = cropped[1:, 1:]
        #
        #     vrho = Physics.get_vrho(t, rho2d, 2)
        #     m_dot = Physics.vrho_mdot(vrho, r_lm(l_lm), 'l')  # r_s = given by the func
        #
        #
        # return Math.combine(t, l_lm, m_dot)

        # return (40.843) + (-15.943*x) + (1.591*x**2)                    # FROM GREY ATMOSPHERE ESTIMATES

        # return -859.098 + 489.056*x - 92.827*x**2 + 5.882*x**3        # FROM SONIC POINT ESTIMATES

    def plot_t_l_mdot(self, l_or_lm, rs, plot_obs, plot_nums, lim_t1 = None, lim_t2 = None):

        # ---------------------LOADING-INTERPOLATED-TABLE---------------------------

        t_k_rho = Save_Load_tables.load_table('t_k_rho', 't', 'k', 'rho', self.opal_used, self.output_dir)
        t_llm_rho = Physics.t_kap_rho_to_t_llm_rho(t_k_rho, l_or_lm)



        #---------------------Getting KAPPA[], T[], RHO2D[]-------------------------

        if rs == 0: # here in *t_llm_r* and in *t_llm_rho*  t, and llm are equivalent
            t_llm_r = self.sp_get_r_lt_table2('r', l_or_lm, True, t_llm_rho)
            t   = t_llm_r[0, 1:]
            llm = t_llm_r[1:,0]
            rs  = t_llm_r[1:,1:]

            t_llm_rho = Math.crop_2d_table(t_llm_rho, t.min(), t.max(), llm.min(), llm.max())
            rho = t_llm_rho[1:, 1:]

            vrho  = Physics.get_vrho(t, rho, 2) # MU assumed constant!
            m_dot = Physics.vrho_mdot(vrho, rs, 'tl')

        else:
            t = t_llm_rho[0, 1:]
            llm = t_llm_rho[1:,0]
            rho = t_llm_rho[1:, 1:]

            vrho = Physics.get_vrho(t, rho, 2)
            m_dot = Physics.vrho_mdot(vrho, rs, '')


        #-------------------------------------------POLT-Ts-LM-MODT-COUTUR------------------------------------

        name = self.plot_dir + 'rs_lm_minMdot_plot.pdf'

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        plt.xlim(t.min(), t.max())
        plt.ylim(llm.min(), llm.max())
        plt.ylabel(Labels.lbls(l_or_lm))
        plt.xlabel(Labels.lbls('ts'))
        levels = [-7.5, -7, -6.5, -6, -5.5, -5, -4.5, -4, -3.5, -3, -2.5, -2]
        contour_filled = plt.contourf(t, llm, m_dot, levels, cmap=plt.get_cmap('RdYlBu_r'))
        plt.colorbar(contour_filled, label=Labels.lbls('mdot'))
        contour = plt.contour(t, llm, m_dot, levels, colors='k')
        plt.clabel(contour, colors='k', fmt='%2.1f', fontsize=12)
        plt.title('SONIC HR DIAGRAM')


        # plt.ylabel(l_or_lm)
        plt.legend(bbox_to_anchor=(0, 0), loc='lower left', ncol=1)
        plt.savefig(name)

        #--------------------------------------------------PLOT-MINS----------------------------------------------------

        # plt.plot(mins[0, :], mins[1, :], '-.', color='red', label='min_Mdot (rs: {} )'.format(r_s_))

        #-----------------------------------------------PLOT-OBSERVABLES------------------------------------------------
        if plot_obs:
            classes = []
            classes.append('dum')
            x = []
            y = []
            for star_n in self.obs.stars_n:
                xyz = self.obs.get_xyz_from_yz(star_n, l_or_lm, 'mdot', t, llm, m_dot, lim_t1, lim_t2)
                if xyz.any():
                    x = np.append(x, xyz[0, 0])
                    y = np.append(y, xyz[1, 0])
                    for i in range(len(xyz[0,:])):
                        plt.plot(xyz[0, i], xyz[1, i], marker=self.obs.get_clss_marker(star_n), markersize='9', color=self.obs.get_class_color(star_n), ls='')  # plot color dots)))
                        ax.annotate(int(star_n), xy=(xyz[0,i], xyz[1,i]),
                                    textcoords='data')  # plot numbers of stars
                        if self.obs.get_star_class(star_n) not in classes:
                            plt.plot(xyz[0, i], xyz[1, i], marker=self.obs.get_clss_marker(star_n), markersize='9', color=self.obs.get_class_color(star_n), ls='', label='{}'.format(self.obs.get_star_class(star_n)))  # plot color dots)))
                            classes.append(self.obs.get_star_class(star_n))

            fit = np.polyfit(x, y, 1)  # fit = set of coeddicients (highest first)
            f = np.poly1d(fit)
            fit_x_coord = np.mgrid[(x.min()-1):(x.max()+1):1000j]
            plt.plot(fit_x_coord, f(fit_x_coord), '-.', color='blue')

        #--------------------------------------------------_NUMERICALS--------------------------------------------------
        if plot_nums:
            for i in range(len(self.sm_files)):
                ts_llm_mdot = self.mdl[i].get_xyz_from_yz(i, 'sp', l_or_lm, 'mdot', t , llm, m_dot, lim_t1, lim_t2)
                # lbl1 = self.mdl[i].get_cond_value(num_var_plot, 'sp')

                if ts_llm_mdot.any():
                    # lbl = 'i:{}, lm:{}, {}:{}'.format(i, "%.2f" % ts_llm_mdot[2, -1], num_var_plot, "%.2f" % lbl1)
                    plt.plot(ts_llm_mdot[0, :], ts_llm_mdot[1,:], marker='x', color='C' + str(Math.get_0_to_max([i],9)[i]), ls='')  # plot color dots)))
                    ax.annotate(str("%.2f" % ts_llm_mdot[2, -1]), xy=(ts_llm_mdot[0, -1], ts_llm_mdot[1,-1]), textcoords='data')

            for i in range(len(self.sm_files)):
                x_coord = self.mdl[i].get_cond_value('t', 'sp')
                y_coord = self.mdl[i].get_cond_value(l_or_lm, 'sp')
                # lbl1 = self.mdl[i].get_cond_value(num_var_plot, 'sp')
                # lbl2 = self.mdl[i].get_cond_value('He4', 'core')

                # lbl = 'i:{}, Yc:{}, {}:{}'.format(i, "%.2f" % lbl2, num_var_plot, "%.2f" % lbl1)
                plt.plot(x_coord, y_coord, marker='X', color='C' + str(Math.get_0_to_max([i], 9)[i]),
                         ls='')  # plot color dots)))
                ax.annotate(str(int(i)), xy=(x_coord, y_coord), textcoords='data')

        plt.legend(bbox_to_anchor=(0, 0), loc='lower left', ncol=1)
        plt.gca().invert_xaxis()
        plt.savefig(name)
        plt.show()

    def min_mdot(self, l_or_lm, rs, plot_obs, plot_nums, plot_sp_crits, lim_t1=5.18, lim_t2=None):
        # ---------------------LOADING-INTERPOLATED-TABLE---------------------------

        t_k_rho = Save_Load_tables.load_table('t_k_rho', 't', 'k', 'rho', self.opal_used, self.output_dir)


        l_lim1, l_lim2 = None, None
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)

        if rs == 0:
            t_llm_mdot = self.empirical_l_r_crit(t_k_rho, l_or_lm)
            t = t_llm_mdot[0, 1:]
            l_lm_arr = t_llm_mdot[1:, 0]
            m_dot = t_llm_mdot[1:, 1:]

            mins = Math.get_mins_in_every_row(t, l_lm_arr, m_dot, 5000, lim_t1, lim_t2)

            plt.plot(mins[2, :], mins[1, :], '-', color='black')
            ax.fill_between(mins[2, :], mins[1, :], color="lightgray")

        else:
            t_llm_rho = Physics.t_kap_rho_to_t_llm_rho(t_k_rho,l_or_lm)

            t = t_llm_rho[0,1:]
            llm = t_llm_rho[1:,0]
            rho = t_llm_rho[1:,1:]

            vrho = Physics.get_vrho(t, rho, 2)       # mu = 1.34 everywhere
            m_dot = Physics.vrho_mdot(vrho, rs, '')  # r_s = constant
            mins = Math.get_mins_in_every_row(t, llm, m_dot, 5000, lim_t1, lim_t2)

            plt.plot(mins[2, :], mins[1, :], '-', color='black')
            ax.fill_between(mins[2, :], mins[1, :], color="lightgray")

        if plot_sp_crits:

            l = []
            m = []
            mdot = []

            for i in range(len(self.sp_files)):
                l   = np.append(l,  self.spmdl[i].get_crit_value('l') )
                m   = np.append(m, self.spmdl[i].get_crit_value('m') )
                mdot= np.append(mdot, self.spmdl[i].get_crit_value('mdot') )

            if l_or_lm == 'l':
                llm_sp = l
            else:
                llm_sp = Physics.loglm(l, m, True)

            plt.plot(mdot, llm_sp, '-', color='red')

        #         sp_file_1 = self.sp_files[0].split('/')[-1]

        if plot_obs:

            classes = []
            classes.append('dum')
            x = []
            y = []

            from Phys_Math_Labels import Opt_Depth_Analythis

            for star_n in self.obs.stars_n:
                i=-1
                x = np.append(x, self.obs.get_num_par('mdot',  star_n))
                y = np.append(y, self.obs.get_num_par(l_or_lm, star_n))
                print(self.obs.get_num_par('mdot',  star_n), self.obs.get_num_par(l_or_lm, star_n))

                plt.plot(x[i], y[i], marker=self.obs.get_clss_marker(star_n), markersize='9',
                         color=self.obs.get_class_color(star_n), ls='')  # plot color dots)))
                # ax.annotate(int(star_n), xy=(x[i], y[i]),
                #             textcoords='data')  # plot numbers of stars

                v_inf = self.obs.get_num_par('v_inf',  star_n)
                tau_cl = Opt_Depth_Analythis(30, v_inf, 1., 1., x[i], 0.20)
                tau = tau_cl.anal_eq_b1(1.)

                ax.annotate(str(int(tau)), xy=(x[i], y[i]),
                            textcoords='data')  # plo

                if self.obs.get_star_class(star_n) not in classes:
                    plt.plot(x[i], y[i], marker=self.obs.get_clss_marker(star_n), markersize='9',
                             color=self.obs.get_class_color(star_n), ls='',
                             label='{}'.format(self.obs.get_star_class(star_n)))  # plot color dots)))
                    classes.append(self.obs.get_star_class(star_n))


            print('\t__PLOT: total stars: {}'.format(len(self.obs.stars_n)))
            print(len(x), len(y))

            # fit = np.polyfit(x, y, 1)  # fit = set of coeddicients (highest first)
            # f = np.poly1d(fit)
            # fit_x_coord = np.mgrid[(x.min() - 1):(x.max() + 1):1000j]
            # plt.plot(fit_x_coord, f(fit_x_coord), '-.', color='blue')

        # --------------------------------------------------NUMERICALS--------------------------------------------------

        if plot_nums:
            for i in range(len(self.sm_files)):
                x_coord = self.mdl[i].get_cond_value('mdot', 'sp')
                y_coord = self.mdl[i].get_cond_value(l_or_lm, 'sp')
                # lbl1 = self.mdl[i].get_cond_value(i, 'sp')
                # lbl2 = self.mdl[i].get_cond_value('He4', 'core')

                # lbl = 'i:{}, Yc:{}, {}:{}'.format(i, "%.2f" % lbl2, num_var_plot, "%.2f" % lbl1)
                plt.plot(x_coord, y_coord, marker='x', color='C' + str(Math.get_0_to_max([i], 9)[i]),
                         ls='')  # plot color dots)))
                ax.annotate(str(int(i)), xy=(x_coord, y_coord),
                            textcoords='data')


        # plt.ylim(y.min(),y.max())

        # plt.xlim(-6.0, mins[2,:].max())

        plt.ylabel(Labels.lbls(l_or_lm))
        plt.xlabel(Labels.lbls('mdot'))
        ax.grid(which='major', alpha=0.2)
        plt.legend(bbox_to_anchor=(1, 1), loc='upper right', ncol=1)

        ax.grid(which='both')
        ax.grid(which='minor', alpha=0.2)
        plt.legend(bbox_to_anchor=(1, 0), loc='lower right', ncol=1)
        plot_name = self.plot_dir + 'minMdot_l.pdf'
        plt.savefig(plot_name)
        plt.show()


#================================================3D=====================================================================
#
#
#================================================3D=====================================================================


from mpl_toolkits.mplot3d.proj3d import proj_transform
from matplotlib.text import Annotation

class Annotation3D(Annotation):
    '''Annotate the point xyz with text s'''

    def __init__(self, s, xyz, *args, **kwargs):
        Annotation.__init__(self,s, xy=(0,0), *args, **kwargs)
        self._verts3d = xyz

    def draw(self, renderer):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj_transform(xs3d, ys3d, zs3d, renderer.M)
        self.xy=(xs,ys)
        Annotation.draw(self, renderer)

class TEST:
    def __init__(self, spfiles, out_dir = '../data/output/', plot_dir = '../data/plots/'):

        self.spfiles = spfiles

        # self.req_name_parts = req_name_parts


        # def select_sp_files(spfile, req_name_parts):
        #
        #     if len(req_name_parts) == 0:
        #         return spfile
        #
        #
        #     no_extens_sp_file = spfile.split('.')[-2]  # getting rid of '.data'
        #
        #     print(spfile, '   ', no_extens_sp_file)
        #
        #     for req_part in req_name_parts:
        #         if req_part in no_extens_sp_file.split('_')[1:]:
        #
        #             return spfile
        #         else:
        #             return None


        self.spmdl = []
        for file in spfiles:
            self.spmdl.append(Read_SP_data_file(file, out_dir, plot_dir))
            # if select_sp_files(file, req_name_parts):
            #     self.spmdl.append( Read_SP_data_file(file, out_dir, plot_dir) )

        print('\t__TEST: total {} files uploaded in total.'.format(len(self.spmdl)))

        self.plot_dit = plot_dir
        self.out_dir = out_dir


    def xy_last_points(self, v_n1, v_n2, v_lbl1, v_lbl_cond, list_of_list_of_smfiles = list(), num_pol_fit = True):
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)

        for j in range(len(list_of_list_of_smfiles)):

            x = []
            y = []
            for i in range(len(list_of_list_of_smfiles[j])):
                sm1 = Read_SM_data_file.from_sm_data_file(list_of_list_of_smfiles[j][i])
                x = np.append(x, sm1.get_cond_value(v_n1, 'sp') )
                y = np.append(y, sm1.get_cond_value(v_n2, 'sp') )

                lbl1 = sm1.get_cond_value(v_lbl1, v_lbl_cond)
                # print(x, y, lbl1)
                #     color='C' + str(Math.get_0_to_max([i],9)[i])
                plt.plot(x[i], y[i], marker='.', color='C' + str(j), ls='', label='{}:{} , {}:{} , {}:{}'
                         .format(v_n1, "%.2f" % x[i], v_n2, "%.2f" % y[i], v_lbl1, "%.2f" % lbl1))  # plot color dots)))
                ax.annotate(str("%.2f" % lbl1), xy=(x[i], y[i]), textcoords='data')

            if num_pol_fit:
                def fitFunc(t, a, b, c, d, e):
                        # return c * np.exp(-b * t ** a) + d
                        return a + t**b + t**c + t**d + e ** t    #
                        # return a + b/t + c/t**2 + d/t**3

                def fitting():
                    from scipy.optimize import curve_fit

                    plt.plot(x, y, 'b.', label='data')
                    popt, pcov = curve_fit(fitFunc, x, y)
                    print(popt)

                    # plt.plot(x, fitFunc(x, *popt), 'r-', label = '' % tuple(popt))
                    x_new = np.mgrid[x[0]:x[-1]:100j]

                    plt.plot(x_new, fitFunc(x_new, popt[0], popt[1], popt[2], popt[3], popt[4]), 'r-')

                # fitting() # - Sophisticated fitting.


                fit = np.polyfit(x, y, 3)  # fit = set of coeddicients (highest first)
                f = np.poly1d(fit)

                # print('Equation:', f.coefficients)
                fit_x_coord = np.mgrid[(x.min()):(x.max()):100j]
                lbl = '{} + {}*x + {}*x**2 + {}*x**3'.format("%.3f" % f.coefficients[3], "%.3f" % f.coefficients[2], "%.3f" % f.coefficients[1], "%.3f" % f.coefficients[0])

                plt.plot(fit_x_coord, f(fit_x_coord), '--', color='black', label=lbl)
                print('smfls1:', lbl)
                print('X:[{} , {}], Y:[{} , {}]'.format("%.3f" % x.min(),  "%.3f" % x.max(), "%.3f" % y.min(), "%.3f" % y.max()))
                # plt.plot(x, f.coefficients[0]*x**3 + f.coefficients[1]*x**2 + f.coefficients[2]*x + f.coefficients[3], 'x', color = 'red')

        name = self.out_dir+'{}_{}_dependance.pdf'.format(v_n2,v_n1)
        plt.title('{} = f({}) plot'.format(v_n2,v_n1))
        plt.xlabel(v_n1)
        plt.ylabel(v_n2)
        plt.legend(bbox_to_anchor=(1, 0), loc='lower right', ncol=1)
        plt.savefig(name)


    def sm_3d_plotting_x_y_z(self, v_n1, v_n2, v_n3, v_lbl1, v_lbl_cond, list_of_list_of_smfiles = list(), num_pol_fit = True):
        from mpl_toolkits.mplot3d import Axes3D


        fig = plt.figure()
        # ax = fig.add_subplot(111, projection='3d')
        ax = fig.gca(projection='3d')


        for j in range(len(list_of_list_of_smfiles)):

            x = []
            y = []
            z = []
            for i in range(len(list_of_list_of_smfiles[j])):
                sm1 = Read_SM_data_file.from_sm_data_file(list_of_list_of_smfiles[j][i])
                x = np.append(x, sm1.get_cond_value(v_n1, 'sp') )
                y = np.append(y, sm1.get_cond_value(v_n2, 'sp') )
                z = np.append(z, sm1.get_cond_value(v_n3, 'sp') )

                lbl1 = sm1.get_cond_value(v_lbl1, v_lbl_cond)

            print(x.shape, y.shape, z.shape)
            # ax.plot_surface(x, y, x, rstride=4, cstride=4, alpha=0.25)

            ax.scatter(x, y, z, c='r', marker='o')
            ax.set_xlabel(Labels.lbls(v_n1))
            ax.set_ylabel(Labels.lbls(v_n2))
            ax.set_zlabel(Labels.lbls(v_n3))



        plt.show()




        # def fitFunc(t, a, b, c, d, e):
        #         # return c * np.exp(-b * t ** a) + d
        #         return a + t**b + t**c + t**d + e ** t    #
        #         # return a + b/t + c/t**2 + d/t**3
        #
        # def myfunc(x, a, b, c):
        #     return a * np.exp(b * x**4) + c*x
        #
        # def fitting():
        #     from scipy.optimize import curve_fit
        #
        #     plt.plot(x, y, 'b.', label='data')
        #     popt, pcov = curve_fit(fitFunc, x, y)
        #     print(popt)
        #
        #     # plt.plot(x, fitFunc(x, *popt), 'r-', label = '' % tuple(popt))
        #     x_new = np.mgrid[x[0]:x[-1]:100j]
        #
        #     plt.plot(x_new, fitFunc(x_new, popt[0], popt[1], popt[2], popt[3], popt[4]), 'r-')
        #
        #     # plt.plot(x, myfunc(x, 1, 1, y[0]))
        #
        #
        #     # t = x# np.linspace(0, 4, 50)
        #     # temp = y# fitFunc(t, 2.5, 1.3, 0.5)
        #     # noisy = temp + 0.05 * np.random.normal(size=len(temp))
        #     # fitParams, fitCovariances = curve_fit(fitFunc, t, noisy)
        #     # print(fitParams)
        #     # print(fitCovariances)
        #     #
        #     # plt.ylabel('Temperature (C)', fontsize=16)
        #     # plt.xlabel('time (s)', fontsize=16)
        #     # plt.xlim(0, 4.1)
        #     # # plot the data as red circles with errorbars in the vertical direction
        #     # plt.errorbar(t, noisy, fmt='ro', yerr=0.2)
        #     # # now plot the best fit curve and also +- 3 sigma curves
        #     # # the square root of the diagonal covariance matrix element
        #     # # is the uncertianty on the corresponding fit parameter.
        #     # sigma = [fitCovariances[0, 0], fitCovariances[1, 1], fitCovariances[2, 2]]
        #     # plt.plot(t, fitFunc(t, fitParams[0], fitParams[1], fitParams[2]),
        #     #          t, fitFunc(t, fitParams[0] + sigma[0], fitParams[1] - sigma[1], fitParams[2] + sigma[2]),
        #     #          t, fitFunc(t, fitParams[0] - sigma[0], fitParams[1] + sigma[1], fitParams[2] - sigma[2])
        #     #          )
        #     plt.show()
        #
        # fitting()
        # save plot to a fil    e
        # savefig('dataFitted.pdf', bbox_inches=0, dpi=600)


        # def fitting()

    def sp_3d_plotting_x_y_z(self, v_n1, v_n2, v_n3, v_n_col):
        from mpl_toolkits.mplot3d import Axes3D

        # fig = plt.subplot(2, 1, 1)


        # fig = plt.subplot(2, 1, 1,)
        # ax1 = plt.subplot(211)
        # ax = fig.add_subplot(111, projection='3d')
        ax = plt.gca(projection='3d')  # fig.gca(projection='3d')
        # ax1 = fig.add_subplot(2, 1, 2, projection='3d')

        all_x = []
        all_y = []
        all_z = []
        all_t = []

        all_x_cr = []
        all_y_cr = []
        all_z_cr = []
        all_t_cr = []


        for i in range(len(self.spfiles)):

            xc = self.spmdl[i].get_crit_value(v_n1)
            yc = self.spmdl[i].get_crit_value(v_n2)
            zc = self.spmdl[i].get_crit_value(v_n3)
            col_c = self.spmdl[i].get_crit_value(v_n_col)

            ax.scatter(xc, yc, zc, color='black', marker='x', linewidths='')


            n_of_rows = len( self.spmdl[i].table[:, 0] ) - 1
            x = []
            y = []
            z = []
            t = []

            for j in range(n_of_rows):
                if self.spmdl[i].get_sonic_cols('r')[j] > 0.:              # selecting only the solutions with found rs
                    x = np.append( x, self.spmdl[i].get_sonic_cols(v_n1)[j] )
                    y = np.append( y, self.spmdl[i].get_sonic_cols(v_n2)[j] )
                    z = np.append( z, self.spmdl[i].get_sonic_cols(v_n3)[j] )
                    t = np.append( t, self.spmdl[i].get_sonic_cols(v_n_col)[j] )

            all_x_cr = np.append(all_x_cr, self.spmdl[i].get_crit_value(v_n1))
            all_y_cr = np.append(all_y_cr, self.spmdl[i].get_crit_value(v_n2))
            all_z_cr = np.append(all_z_cr, self.spmdl[i].get_crit_value(v_n3))
            all_t_cr = np.append(all_t_cr, self.spmdl[i].get_crit_value(v_n_col))

            x = np.append(x, all_x_cr) # adding critical values
            y = np.append(y, all_y_cr)
            z = np.append(z, all_z_cr)
            t = np.append(t, all_t_cr)

            all_x = np.append(all_x, x)
            all_y = np.append(all_y, y)
            all_z = np.append(all_z, z)
            all_t = np.append(all_t, t)

            # ax.scatter(x, y, z, c=t, marker='o', cmap=plt.get_cmap('RdYlBu_r'))



        # ---------------------------------------------------------------------------------------

        print(len(all_x), len(all_y), len(all_z), len(all_t))

        sc = ax.scatter(all_x, all_y, all_z, c=all_t, marker='o', cmap=plt.get_cmap('Purples_r'))

        plt.colorbar(sc, label=Labels.lbls(v_n_col))

        # ax = fig.add_subplot(111, projection='3d')
        # ax.plot(all_x, all_z, 'r.', zdir='y', zs = all_y.max() - all_y.max()/2)
        # ax.plot(all_y, all_z, 'g.', zdir='x', zs = all_x.max() - all_x.max()/20)
        # ax.plot(all_x, all_y, 'k.', zdir='z', zs = all_z.max() - all_z.max())

        # ax.plot(all_x, all_z, 'r.', zdir='y', zs = all_y.min())
        # ax.plot(all_y, all_z, 'g.', zdir='x', zs = all_x.min())
        # ax.plot(all_x, all_y, 'k.', zdir='z', zs = all_z.min())


        # --- --- --- SUBPLOTS --- --- ---

        # ax1 = fig.add_subplot(1, 1, 1)
        # plt.plot(all_x, all_y, '.')


        ax.w_xaxis.set_pane_color((0.4, 0.4, 0.6, 0.3))
        ax.w_yaxis.set_pane_color((0.4, 0.4, 0.6, 0.3))
        ax.w_zaxis.set_pane_color((0.4, 0.4, 0.6, 0.3))

        ax.set_xlabel(Labels.lbls(v_n1))
        ax.set_ylabel(Labels.lbls(v_n2))
        ax.set_zlabel(Labels.lbls(v_n3))

        plt.show()
        # fig.canvas.show()

        # def fitFunc(t, a, b, c, d, e):
        #         # return c * np.exp(-b * t ** a) + d
        #         return a + t**b + t**c + t**d + e ** t    #
        #         # return a + b/t + c/t**2 + d/t**3
        #
        # def myfunc(x, a, b, c):
        #     return a * np.exp(b * x**4) + c*x
        #
        # def fitting():
        #     from scipy.optimize import curve_fit
        #
        #     plt.plot(x, y, 'b.', label='data')
        #     popt, pcov = curve_fit(fitFunc, x, y)
        #     print(popt)
        #
        #     # plt.plot(x, fitFunc(x, *popt), 'r-', label = '' % tuple(popt))
        #     x_new = np.mgrid[x[0]:x[-1]:100j]
        #
        #     plt.plot(x_new, fitFunc(x_new, popt[0], popt[1], popt[2], popt[3], popt[4]), 'r-')
        #
        #     # plt.plot(x, myfunc(x, 1, 1, y[0]))
        #
        #
        #     # t = x# np.linspace(0, 4, 50)
        #     # temp = y# fitFunc(t, 2.5, 1.3, 0.5)
        #     # noisy = temp + 0.05 * np.random.normal(size=len(temp))
        #     # fitParams, fitCovariances = curve_fit(fitFunc, t, noisy)
        #     # print(fitParams)
        #     # print(fitCovariances)
        #     #
        #     # plt.ylabel('Temperature (C)', fontsize=16)
        #     # plt.xlabel('time (s)', fontsize=16)
        #     # plt.xlim(0, 4.1)
        #     # # plot the data as red circles with errorbars in the vertical direction
        #     # plt.errorbar(t, noisy, fmt='ro', yerr=0.2)
        #     # # now plot the best fit curve and also +- 3 sigma curves
        #     # # the square root of the diagonal covariance matrix element
        #     # # is the uncertianty on the corresponding fit parameter.
        #     # sigma = [fitCovariances[0, 0], fitCovariances[1, 1], fitCovariances[2, 2]]
        #     # plt.plot(t, fitFunc(t, fitParams[0], fitParams[1], fitParams[2]),
        #     #          t, fitFunc(t, fitParams[0] + sigma[0], fitParams[1] - sigma[1], fitParams[2] + sigma[2]),
        #     #          t, fitFunc(t, fitParams[0] - sigma[0], fitParams[1] + sigma[1], fitParams[2] - sigma[2])
        #     #          )
        #     plt.show()
        #
        # fitting()
        # save plot to a fil    e
        # savefig('dataFitted.pdf', bbox_inches=0, dpi=600)


        # def fitting()

    def sp_3d_and_multiplot(self, v_n1, v_n2, v_n3, v_n_col, sp_or_crit = 'both'):

        all_x = []
        all_y = []
        all_z = []
        all_t = []

        all_x_cr = []
        all_y_cr = []
        all_z_cr = []
        all_t_cr = []

        # set up a figure twice as wide as it is tall
        fig = plt.figure(figsize=plt.figaspect(1.0))

        # ===============
        # First subplot
        # ===============

        ax = fig.add_subplot(221, projection='3d')  # ax = fig.add_subplot(1, 2, 1, projection='3d') for 2 plots

        for i in range(len(self.spmdl)):

            xc = self.spmdl[i].get_crit_value(v_n1)
            yc = self.spmdl[i].get_crit_value(v_n2)
            zc = self.spmdl[i].get_crit_value(v_n3)
            col_c = self.spmdl[i].get_crit_value(v_n_col)

            ax.scatter(xc, yc, zc, color='black', marker='x', linewidths='')

            n_of_rows = len(self.spmdl[i].table[:, 0]) - 1
            x = []
            y = []
            z = []
            t = []


            if sp_or_crit == 'sp' or sp_or_crit == 'both':
                for j in range(n_of_rows):
                    if self.spmdl[i].get_sonic_cols('r')[j] > 0.:  # selecting only the solutions with found rs
                        x = np.append(x, self.spmdl[i].get_sonic_cols(v_n1)[j])
                        y = np.append(y, self.spmdl[i].get_sonic_cols(v_n2)[j])
                        z = np.append(z, self.spmdl[i].get_sonic_cols(v_n3)[j])
                        t = np.append(t, self.spmdl[i].get_sonic_cols(v_n_col)[j])

            if sp_or_crit == 'crit' or sp_or_crit == 'both':
                all_x_cr = np.append(all_x_cr, self.spmdl[i].get_crit_value(v_n1))
                all_y_cr = np.append(all_y_cr, self.spmdl[i].get_crit_value(v_n2))
                all_z_cr = np.append(all_z_cr, self.spmdl[i].get_crit_value(v_n3))
                all_t_cr = np.append(all_t_cr, self.spmdl[i].get_crit_value(v_n_col))

            x = np.append(x, all_x_cr)  # adding critical values
            y = np.append(y, all_y_cr)
            z = np.append(z, all_z_cr)
            t = np.append(t, all_t_cr)

            all_x = np.append(all_x, x)
            all_y = np.append(all_y, y)
            all_z = np.append(all_z, z)
            all_t = np.append(all_t, t)

        sc = ax.scatter(all_x, all_y, all_z, c=all_t, marker='o', cmap=plt.get_cmap('Spectral'))

        clb = plt.colorbar(sc)
        clb.ax.set_title(Labels.lbls(v_n_col))


        ax.w_xaxis.set_pane_color((0.4, 0.4, 0.6, 0.3))
        ax.w_yaxis.set_pane_color((0.4, 0.4, 0.6, 0.3))
        ax.w_zaxis.set_pane_color((0.4, 0.4, 0.6, 0.3))

        ax.set_xlabel(Labels.lbls(v_n1))
        ax.set_ylabel(Labels.lbls(v_n2))
        ax.set_zlabel(Labels.lbls(v_n3))

        # ===============
        # Second subplots
        # ===============

        ax = fig.add_subplot(222)
        ax.grid()
        sc = ax.scatter(all_x_cr, all_y_cr, c=all_t_cr, marker='o', cmap=plt.get_cmap('Spectral'))
        ax.set_xlabel(Labels.lbls(v_n1))
        ax.set_ylabel(Labels.lbls(v_n2))
        for i in range(len(all_x_cr)):
            ax.annotate("%.2f" % all_t_cr[i], xy=(all_x_cr[i], all_y_cr[i]), textcoords='data')  # plot numbers of stars
        clb = plt.colorbar(sc)
        clb.ax.set_title(Labels.lbls(v_n_col))


        ax = fig.add_subplot(223)
        ax.grid()
        sc = ax.scatter(all_y_cr, all_z_cr, c=all_t_cr, marker='o', cmap=plt.get_cmap('Spectral'))
        ax.set_xlabel(Labels.lbls(v_n2))
        ax.set_ylabel(Labels.lbls(v_n3))
        for i in range(len(all_x_cr)):
            ax.annotate("%.2f" % all_t_cr[i], xy=(all_y_cr[i], all_z_cr[i]), textcoords='data')  # plot numbers of stars
        clb = plt.colorbar(sc)
        clb.ax.set_title(Labels.lbls(v_n_col))


        ax = fig.add_subplot(224)
        ax.grid()
        sc = ax.scatter(all_x_cr, all_z_cr, c=all_t_cr, marker='o', cmap=plt.get_cmap('Spectral'))
        ax.set_xlabel(Labels.lbls(v_n1))
        ax.set_ylabel(Labels.lbls(v_n3))
        for i in range(len(all_x_cr)):
            ax.annotate("%.2f" % all_t_cr[i], xy=(all_x_cr[i], all_z_cr[i]), textcoords='data')  # plot numbers of stars
        clb = plt.colorbar(sc)
        clb.ax.set_title(Labels.lbls(v_n_col))



        plt.show()


    def new_3d(self):

        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import axes3d
        from mpl_toolkits.mplot3d.art3d import Line3DCollection


        def annotate3D(ax, s, *args, **kwargs):
            '''add anotation text s to to Axes3d ax'''

            tag = Annotation3D(s, *args, **kwargs)
            ax.add_artist(tag)



        # data: coordinates of nodes and links
        xn = [1.1, 1.9, 0.1, 0.3, 1.6, 0.8, 2.3, 1.2, 1.7, 1.0, -0.7, 0.1, 0.1, -0.9, 0.1, -0.1, 2.1, 2.7, 2.6, 2.0]
        yn = [-1.2, -2.0, -1.2, -0.7, -0.4, -2.2, -1.0, -1.3, -1.5, -2.1, -0.7, -0.3, 0.7, -0.0, -0.3, 0.7, 0.7, 0.3,
              0.8, 1.2]
        zn = [-1.6, -1.5, -1.3, -2.0, -2.4, -2.1, -1.8, -2.8, -0.5, -0.8, -0.4, -1.1, -1.8, -1.5, 0.1, -0.6, 0.2, -0.1,
              -0.8, -0.4]
        group = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 2, 2, 2, 3, 3, 3, 3]
        edges = [(1, 0), (2, 0), (3, 0), (3, 2), (4, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (11, 10), (11, 3),
                 (11, 2), (11, 0), (12, 11), (13, 11), (14, 11), (15, 11), (17, 16), (18, 16), (18, 17), (19, 16),
                 (19, 17), (19, 18)]

        xyzn = zip(xn, yn, zn)
        segments = [(list(xyzn)[s], list(xyzn)[t]) for s, t in edges]

        # create figure
        fig = plt.figure(dpi=60)
        ax = fig.gca(projection='3d')
        ax.set_axis_off()

        # plot vertices
        ax.scatter(xn, yn, zn, marker='o', c=group, s=64)
        # plot edges
        edge_col = Line3DCollection(segments, lw=0.2)
        ax.add_collection3d(edge_col)
        # add vertices annotation.
        for j, xyz_ in enumerate(xyzn):
            annotate3D(ax, s=str(j), xyz=xyz_, fontsize=10, xytext=(-3, 3),
                       textcoords='offset points', ha='right', va='bottom')
        plt.show()