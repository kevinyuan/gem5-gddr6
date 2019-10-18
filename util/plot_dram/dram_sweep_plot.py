#!/usr/bin/env python2.7

# Copyright (c) 2014 ARM Limited
# All rights reserved
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Andreas Hansson

try:
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib import cm
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print "Failed to import matplotlib and numpy"
    exit(-1)

import sys
import re

# Determine the parameters of the sweep from the simout output, and
# then parse the stats and plot the 3D surface corresponding to the
# different combinations of parallel banks, and stride size, as
# generated by the config/dram/sweep.py script
def main():

    if len(sys.argv) != 3:
        print "Usage: ", sys.argv[0], "-u|p|e <simout directory>"
        exit(-1)

    if len(sys.argv[1]) != 2 or sys.argv[1][0] != '-' or \
            not sys.argv[1][1] in "upe":
        print "Choose -u (utilisation), -p (total power), or -e " \
            "(power efficiency)"
        exit(-1)

    # Choose the appropriate mode, either utilisation, total power, or
    # efficiency
    mode = sys.argv[1][1]

    try:
        stats = open(sys.argv[2] + '/stats.txt', 'r')
    except IOError:
        print "Failed to open ", sys.argv[2] + '/stats.txt', " for reading"
        exit(-1)

    try:
        simout = open(sys.argv[2] + '/simout', 'r')
    except IOError:
        print "Failed to open ", sys.argv[2] + '/simout', " for reading"
        exit(-1)

    # Get the burst size, number of banks and the maximum stride from
    # the simulation output
    got_sweep = False

    for line in simout:
        match = re.match("DRAM sweep with "
                         "burst: (\d+), banks: (\d+), max stride: (\d+)", line)
        if match:
            burst_size = int(match.groups(0)[0])
            banks = int(match.groups(0)[1])
            max_size = int(match.groups(0)[2])
            got_sweep = True

    simout.close()

    if not got_sweep:
        print "Failed to establish sweep details, ensure simout is up-to-date"
        exit(-1)

    # Now parse the stats
    peak_bw = []
    bus_util = []
    avg_pwr = []

    for line in stats:
        match = re.match(".*busUtil\s+(\d+\.\d+)\s+#.*", line)
        if match:
            bus_util.append(float(match.groups(0)[0]))

        match = re.match(".*peakBW\s+(\d+\.\d+)\s+#.*", line)
        if match:
            peak_bw.append(float(match.groups(0)[0]))

        match = re.match(".*averagePower\s+(\d+\.?\d*)\s+#.*", line)
        if match:
            avg_pwr.append(float(match.groups(0)[0]))
    stats.close()


    # print "Length of Peak bandwidth = %d, bus utilisation = %d, and average
    # power = %d\n" % (len(peak_bw), len(bus_util), len(avg_pwr))

    # Sanity check
    if not (len(peak_bw) == len(bus_util) and len(bus_util) == len(avg_pwr)):
        print "Peak bandwidth, bus utilisation, and average power do not match"
        exit(-1)

    # Collect the selected metric as our Z-axis, we do this in a 2D
    # grid corresponding to each iteration over the various stride
    # sizes.
    z = []
    zs = []
    i = 0

    for j in range(len(peak_bw)):
        if mode == 'u':
            z.append(bus_util[j])
        elif mode == 'p':
            z.append(avg_pwr[j])
        elif mode == 'e':
            # avg_pwr is in mW, peak_bw in MiByte/s, bus_util in percent
            z.append(avg_pwr[j] / (bus_util[j] / 100.0 * peak_bw[j] / 1000.0))
        else:
            print "Unexpected mode %s" % mode
            exit(-1)

        i += 1
        # If we have completed a sweep over the stride sizes,
        # start anew
        # Put every 8 samples in another dimension (bank)
        # One or more last n samples in z[] may be discard
        #if i == max_size / (burst_size):
        #    zs.append(z)
        #    z = []
        #    i = 0

        #print " j = %d, i = %d " % (j, i)

    #print "zs = %d, bank = %d" % (len(zs), banks)

    # We should have a 2D grid with as many columns as banks
#    if len(zs) != banks:
#        print "Unexpected number of data points in stats output: zs = %d, bank
#        = %d" % (len(zs), banks)
#        exit(-1)

    fig = plt.figure()
    #ax = fig.gca(projection='3d')
    X = np.arange(burst_size, max_size + 1, burst_size)
    z = np.resize(z, np.size(X))
    #print "X:", X
    #print "zs:", z

    Y = np.arange(1, banks + 1, 1)
    #X, Y = np.meshgrid(X, Y)

    # the values in the util are banks major, so we see groups for each
    # stride size in order
    #Z = np.array(zs)

#    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
#                           linewidth=0, antialiased=False)

    plt.plot(X, z, '-o')

    for i,j in zip(X,z):
        jj = round(512*j/100,2)
        plt.text(i-8, j+2, '   ' + str(j)+'%\n('+str(jj)+' Gbps)')

    plt.xticks(np.arange(0, 512 + 1, 64))

    plt.ylim(0, 100)

    plt.xlabel('Access length (Bytes)')
    plt.ylabel('Utilisation (%)')

#
#    if mode == 'u':
#        ax.set_zlabel('Utilisation (%)')
#    elif mode == 'p':
#        ax.set_zlabel('Power (mW)')
#    elif mode == 'e':
#        ax.set_zlabel('Power efficiency (mW / GByte / s)')
#
#    # Add a colorbar
#    fig.colorbar(surf, shrink=0.5, pad=.1, aspect=10)

    plt.show()

if __name__ == "__main__":
    main()
