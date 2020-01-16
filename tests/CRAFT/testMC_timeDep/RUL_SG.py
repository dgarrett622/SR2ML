from scipy.stats import norm
from scipy.integrate import quad
import random
import numpy as np

def RULmodel(mu,sigma,time):
  prob = norm.cdf(time, mu, sigma)
  return prob


def run(self,Input):
  # intput: alpha, beta
  # output: t, p
  self.p_SG = np.zeros(len(self.time))

  updatedMean  = (Input['alpha_SG']-50.) * 365.
  updatedsigma = Input['beta_SG']  * 365.

  for ts in range(len(self.time)):
    self.p_SG[ts] = RULmodel(updatedMean, updatedsigma, self.time[ts])

