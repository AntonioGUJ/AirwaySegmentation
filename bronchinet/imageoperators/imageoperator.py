
from typing import Tuple
import numpy as np

from scipy.ndimage.morphology import binary_fill_holes, binary_erosion, binary_dilation, binary_opening, binary_closing
from skimage.transform import rescale
from skimage.morphology import skeletonize_3d
from skimage.measure import label
# from scipy.misc import imresize

BoundBox2DType = Tuple[Tuple[int, int], Tuple[int, int]]
BoundBox3DType = Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]


class ImageOperator(object):

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        raise NotImplementedError


class NormaliseImage(ImageOperator):

    @staticmethod
    def _compute_nochannels(in_image: np.ndarray) -> np.ndarray:
        max_value = np.max(in_image)
        min_value = np.min(in_image)
        return (in_image - min_value) / float(max_value - min_value)

    @staticmethod
    def _compute_withchannels(in_image: np.ndarray) -> np.ndarray:
        num_channels = in_image.shape[-1]
        for i in range(num_channels):
            max_value = np.max(in_image[..., i])
            min_value = np.min(in_image[..., i])
            in_image[..., i] = (in_image[..., i] - min_value) / float(max_value - min_value)
        return in_image

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        is_with_channels = kwargs['is_with_channels'] if 'is_with_channels' in kwargs.keys() else False
        if is_with_channels:
            return cls._compute_withchannels(in_image)
        else:
            return cls._compute_nochannels(in_image)


class CropImage(ImageOperator):

    @staticmethod
    def _compute2d(in_image: np.ndarray,
                   in_boundbox: BoundBox2DType
                   ) -> np.ndarray:
        return in_image[in_boundbox[0][0]:in_boundbox[0][1], in_boundbox[1][0]:in_boundbox[1][1],
                        ...]    # last dim for channels

    @staticmethod
    def _compute3d(in_image: np.ndarray,
                   in_boundbox: BoundBox3DType
                   ) -> np.ndarray:
        return in_image[in_boundbox[0][0]:in_boundbox[0][1], in_boundbox[1][0]:in_boundbox[1][1],
                        in_boundbox[2][0]:in_boundbox[2][1], ...]    # last dim for channels

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        is_image2d = kwargs['is_image_2D'] if 'is_image_2D' in kwargs.keys() else False
        if is_image2d:
            return cls._compute2d(in_image, *args)
        else:
            return cls._compute3d(in_image, *args)


class SetPatchInImage(ImageOperator):

    @staticmethod
    def _compute2d(in_image: np.ndarray, out_image: np.ndarray,
                   in_boundbox: BoundBox2DType
                   ) -> np.ndarray:
        out_image[in_boundbox[0][0]:in_boundbox[0][1], in_boundbox[1][0]:in_boundbox[1][1],
                  ...] = in_image   # last dim for channels
        return out_image

    @staticmethod
    def _compute_add2d(in_image: np.ndarray, out_image: np.ndarray,
                       in_boundbox: BoundBox2DType
                       ) -> np.ndarray:
        out_image[in_boundbox[0][0]:in_boundbox[0][1], in_boundbox[1][0]:in_boundbox[1][1],
                  ...] += in_image  # last dim for channels
        return out_image

    @staticmethod
    def _compute3d(in_image: np.ndarray, out_image: np.ndarray,
                   in_boundbox: BoundBox3DType
                   ) -> np.ndarray:
        out_image[in_boundbox[0][0]:in_boundbox[0][1], in_boundbox[1][0]:in_boundbox[1][1],
                  in_boundbox[2][0]:in_boundbox[2][1], ...] = in_image   # last dim for channels
        return out_image

    @staticmethod
    def _compute_add3d(in_image: np.ndarray, out_image: np.ndarray,
                       in_boundbox: BoundBox3DType
                       ) -> np.ndarray:
        out_image[in_boundbox[0][0]:in_boundbox[0][1], in_boundbox[1][0]:in_boundbox[1][1],
                  in_boundbox[2][0]:in_boundbox[2][1], ...] += in_image  # last dim for channels
        return out_image

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        is_image2d = kwargs['is_image_2D'] if 'is_image_2D' in kwargs.keys() else False
        is_calc_add = kwargs['is_calc_add'] if 'is_calc_add' in kwargs.keys() else False
        if is_image2d:
            if is_calc_add:
                return cls._compute_add2d(in_image, *args)
            else:
                return cls._compute2d(in_image, *args)
        else:
            if is_calc_add:
                return cls._compute_add3d(in_image, *args)
            else:
                return cls._compute3d(in_image, *args)


class CropImageAndSetPatchInImage(ImageOperator):

    @staticmethod
    def _compute2d(in_image: np.ndarray, out_image: np.ndarray,
                   in_crop_boundbox: BoundBox2DType,
                   in_extend_boundbox: BoundBox2DType
                   ) -> np.ndarray:
        return SetPatchInImage._compute2d(CropImage._compute2d(in_image, in_crop_boundbox),
                                          out_image, in_extend_boundbox)

    @staticmethod
    def _compute3d(in_image: np.ndarray, out_image: np.ndarray,
                   in_crop_boundbox: BoundBox3DType,
                   in_extend_boundbox: BoundBox3DType
                   ) -> np.ndarray:
        return SetPatchInImage._compute3d(CropImage._compute3d(in_image, in_crop_boundbox),
                                          out_image, in_extend_boundbox)

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        is_image2d = kwargs['is_image_2D'] if 'is_image_2D' in kwargs.keys() else False
        if is_image2d:
            return cls._compute2d(in_image, *args)
        else:
            return cls._compute3d(in_image, *args)


class ExtendImage(ImageOperator):

    @staticmethod
    def _get_init_output(out_shape: Tuple[int, ...], out_dtype: np.dtype, value_backgrnd: float = None) -> np.ndarray:
        if value_backgrnd is None:
            return np.zeros(out_shape, dtype=out_dtype)
        else:
            return np.full(out_shape, value_backgrnd, dtype=out_dtype)

    @classmethod
    def _compute2d(cls, in_image: np.ndarray,
                   in_boundbox: BoundBox2DType,
                   out_shape_image: Tuple[int, int],
                   value_backgrnd: float = None
                   ) -> np.ndarray:
        if value_backgrnd is None:
            value_backgrnd = in_image[0][0]

        out_image = cls._get_init_output(out_shape_image, in_image.dtype, value_backgrnd)
        SetPatchInImage._compute2d(in_image, out_image, in_boundbox)
        return out_image

    @classmethod
    def _compute3d(cls,
                   in_image: np.ndarray,
                   in_boundbox: BoundBox3DType,
                   out_shape_image: Tuple[int, int, int],
                   value_backgrnd: float = None
                   ) -> np.ndarray:
        if value_backgrnd is None:
            value_backgrnd = in_image[0][0][0]

        out_image = cls._get_init_output(out_shape_image, in_image.dtype, value_backgrnd)
        SetPatchInImage._compute3d(in_image, out_image, in_boundbox)
        return out_image

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        is_image2d = kwargs['is_image_2D'] if 'is_image_2D' in kwargs.keys() else False
        if is_image2d:
            return cls._compute2d(in_image, *args)
        else:
            return cls._compute3d(in_image, *args)


class CropAndExtendImage(ImageOperator):

    @staticmethod
    def _compute2d(in_image: np.ndarray,
                   in_crop_boundbox: BoundBox2DType,
                   in_extend_boundbox: BoundBox2DType,
                   out_shape_image: Tuple[int, int],
                   value_backgrnd: float = None
                   ) -> np.ndarray:
        if value_backgrnd is None:
            value_backgrnd = in_image[0][0]
        return ExtendImage._compute2d(CropImage._compute2d(in_image, in_crop_boundbox),
                                      in_extend_boundbox,
                                      out_shape_image,
                                      value_backgrnd)

    @staticmethod
    def _compute3d(in_image: np.ndarray,
                   in_crop_boundbox: BoundBox3DType,
                   in_extend_boundbox: BoundBox3DType,
                   out_shape_image: Tuple[int, int, int],
                   value_backgrnd: float = None
                   ) -> np.ndarray:
        if value_backgrnd is None:
            value_backgrnd = in_image[0][0][0]
        return ExtendImage._compute3d(CropImage._compute3d(in_image, in_crop_boundbox),
                                      in_extend_boundbox,
                                      out_shape_image,
                                      value_backgrnd)

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        is_image2d = kwargs['is_image_2D'] if 'is_image_2D' in kwargs.keys() else False
        if is_image2d:
            return cls._compute2d(in_image, *args)
        else:
            return cls._compute3d(in_image, *args)


class RescaleImage(ImageOperator):
    _order_default = 3

    @staticmethod
    def _compute(in_image: np.ndarray,
                 scale_factor: Tuple[int, ...],
                 order: int = _order_default,
                 is_inlabels: bool = False,
                 is_binary_output: bool = False
                 ) -> np.ndarray:
        if is_inlabels:
            out_image = rescale(in_image, scale=scale_factor, order=order,
                                preserve_range=True, multichannel=False, anti_aliasing=True)
            if is_binary_output:
                # remove noise due to interpolation
                thres_remove_noise = 0.1
                return ThresholdImage.compute(out_image, thres_val=thres_remove_noise)
            else:
                return out_image
        else:
            return rescale(in_image, scale=scale_factor, order=order,
                           preserve_range=True, multichannel=False, anti_aliasing=True)

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        return cls._compute(in_image, *args, **kwargs)


class FlipImage(ImageOperator):

    @staticmethod
    def _compute2d(in_image: np.ndarray, axis: int) -> np.ndarray:
        if axis == 0:
            return in_image[::-1, :]
        elif axis == 1:
            return in_image[:, ::-1]
        else:
            return False

    @staticmethod
    def _compute3d(in_image: np.ndarray, axis: int) -> np.ndarray:
        if axis == 0:
            return in_image[::-1, :, :]
        elif axis == 1:
            return in_image[:, ::-1, :]
        elif axis == 2:
            return in_image[:, :, ::-1]
        else:
            return False

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        axis = kwargs['axis'] if 'axis' in kwargs.keys() else 0
        is_image2d = kwargs['is_image_2D'] if 'is_image_2D' in kwargs.keys() else False
        if is_image2d:
            return cls._compute2d(in_image, axis=axis)
        else:
            return cls._compute3d(in_image, axis=axis)


class ThresholdImage(ImageOperator):
    _value_mask = 1
    _value_backgrnd = 0

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        threshold_val = args[0]
        return np.where(in_image > threshold_val, cls._value_mask, cls._value_backgrnd).astype(np.uint8)


class ThinningMask(ImageOperator):
    # Thinning mask to obtain Centrelines

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        return skeletonize_3d(in_image.astype(np.uint8))


class VolumeMask(ImageOperator):

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        voxel_size = kwargs['voxel_size'] if 'voxel_size' in kwargs.keys() else None
        masks_sum = np.sum(in_image)
        if voxel_size:
            voxel_vol = np.prod(voxel_size)
            return masks_sum * voxel_vol
        else:
            return masks_sum


class MorphoFillHolesMask(ImageOperator):

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        return binary_fill_holes(in_image).astype(in_image.dtype)


class MorphoErodeMask(ImageOperator):

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        num_iters = kwargs['num_iters'] if 'num_iters' in kwargs.keys() else 1
        return binary_erosion(in_image, iterations=num_iters).astype(in_image.dtype)


class MorphoDilateMask(ImageOperator):

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        num_iters = kwargs['num_iters'] if 'num_iters' in kwargs.keys() else 1
        return binary_dilation(in_image, iterations=num_iters).astype(in_image.dtype)


class MorphoOpenMask(ImageOperator):

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        num_iters = kwargs['num_iters'] if 'num_iters' in kwargs.keys() else 1
        return binary_opening(in_image, iterations=num_iters).astype(in_image.dtype)


class MorphoCloseMask(ImageOperator):

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        num_iters = kwargs['num_iters'] if 'num_iters' in kwargs.keys() else 1
        return binary_closing(in_image, iterations=num_iters).astype(in_image.dtype)


class ConnectedRegionsMask(ImageOperator):

    @staticmethod
    def _compute_calc(in_image: np.ndarray, connectivity_dim: int) -> np.ndarray:
        out_image = label(in_image,
                          connectivity=connectivity_dim,
                          background=0)
        return out_image.astype(in_image.dtype)

    @staticmethod
    def compute_get_num_regs(in_image: np.ndarray, connectivity_dim: int = None) -> Tuple[np.ndarray, int]:
        if connectivity_dim is None:
            connectivity_dim = in_image.ndim
        (out_image, out_num_regs) = label(in_image,
                                          connectivity=connectivity_dim,
                                          background=0,
                                          return_num=True)
        return (out_image.astype(in_image.dtype), out_num_regs)

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        connectivity_dim = kwargs['connectivity_dim'] if 'connectivity_dim' in kwargs.keys() else in_image.ndim
        return cls._compute_calc(in_image, connectivity_dim)


class FirstConnectedRegionMask(ImageOperator):

    @classmethod
    def compute(cls, in_image: np.ndarray, *args, **kwargs) -> np.ndarray:
        connectivity_dim = kwargs['connectivity_dim'] if 'connectivity_dim' in kwargs.keys() else in_image.ndim
        (all_regions, num_regs) = ConnectedRegionsMask.compute_get_num_regs(in_image, connectivity_dim)

        # retrieve the conn. region with the largest volume
        max_vol_regs = 0.0
        out_image = None
        for ireg in range(num_regs):
            # volume = count voxels for the the conn. region with label "i+1"
            iconreg_vol = np.count_nonzero(all_regions == ireg + 1)
            if iconreg_vol > max_vol_regs:
                # extract the conn. region with label "i+1"
                out_image = np.where(all_regions == ireg + 1, 1, 0).astype(in_image.dtype)
                max_vol_regs = iconreg_vol

        return out_image
