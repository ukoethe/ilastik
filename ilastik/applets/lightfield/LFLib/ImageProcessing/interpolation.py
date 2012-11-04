import libinterpolation as fast


def bilinear_2d(im,sample_y,sample_x):
  return fast._bilinear_2d(im,sample_y,sample_x)