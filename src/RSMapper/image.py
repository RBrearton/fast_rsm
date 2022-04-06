"""
This module contains the class that is used to store images.
"""

import numpy as np

from .metadata import Metadata
from .motors import Motors


class Image:
    """
    The class used to store raw image data. Internally, this data is stored as
    a numpy array.

    Attrs:
        data:
            A numpy array storing the image data.
    """

    def __init__(self, raw_data: np.ndarray, motors: Motors, metadata: Metadata):
        self._raw_data = raw_data
        self.motors = motors
        self.metadata = metadata

        self._delta_q = None

        # Carry out transposes etc. if necessary:
        # We want self.data[0, 0] to be the top left pixel.
        # We want self.data[-1, 0] to be th top right pixel.
        self._correct_img_axes()

    def _correct_img_axes(self):
        """
        Correct the image axes so that the image is the right way around, taking
        transposes if necessary. This method can use the metadata to work out
        where the data came from so that different transposes/inversions can be
        carried out depending on where the data was acquired.
        """
        raise NotImplementedError()

    @property
    def data(self):
        """
        Returns the normalized data.
        """
        return self._raw_data/self.metadata.solid_angles

    @property
    def pixel_theta(self):
        """
        Returns the theta value at each pixel.
        """
        return self.metadata.relative_theta + self.motors.theta

    @property
    def pixel_phi(self):
        """
        Returns the phi value at each pixel.
        """
        return self.metadata.relative_phi + self.motors.phi

    @property
    def q_out(self) -> np.ndarray:
        """
        Returns the q vectors of the light after scattering to each pixel on the
        detector.
        """
        q_z = np.zeros_like(self.delta_q)
        q_z[:, :, 2] = self.metadata.q_incident_lenth
        return self.delta_q + q_z

    @property
    def delta_q(self) -> np.ndarray:
        """
        Returns the q vectors through which light had to scatter to reach each
        pixel.
        """
        if self._delta_q is None:
            self._init_delta_q()
        return self._delta_q

    def _init_delta_q(self) -> None:
        """
        Sets the self._delta_q attribute for this instance of Image.
        """
        # We need num_x_pixels, num_y_pixels, 3 to be our shape.
        # Note that we need the extra "3" to store qx, qy, qz (3d vector).
        desired_shape = tuple(list(self._raw_data.shape).append(3))
        delta_q = np.zeros(desired_shape)

        # Now set the elements of the delta q matrix element.
        # First set all the delta_q_x values, then delta_q_y, then delta_q_z.
        delta_q[:, :, 0] = np.sin(self.pixel_phi)
        delta_q[:, :, 1] = np.cos(self.pixel_phi) * np.sin(self.pixel_theta)
        delta_q[:, :, 2] = np.cos(self.pixel_phi) * np.cos(self.pixel_theta)-1
        delta_q *= self.metadata.q_incident_lenth

        self._delta_q = delta_q