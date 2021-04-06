
from typing import Tuple
import numpy as np
from scipy.spatial import distance
# from scipy.stats import signaltonoise
from skimage.metrics import structural_similarity as ssim

_EPS = 1.0e-7
_SMOOTH = 1.0

LIST_AVAIL_METRICS = ['MeanSquaredError',
                      'MeanSquaredErrorLogarithmic',
                      'BinaryCrossEntropy',
                      'WeightedBinaryCrossEntropy',
                      'WeightedBinaryCrossEntropyFixedWeights',
                      'DiceCoefficient',
                      'TruePositiveRate',
                      'TrueNegativeRate',
                      'FalsePositiveRate',
                      'FalseNegativeRate',
                      'AirwayCompleteness',
                      'AirwayVolumeLeakage',
                      'AirwayCentrelineLeakage',
                      'AirwayTreeLength',
                      'AirwayCentrelineDistanceFalsePositiveError',
                      'AirwayCentrelineDistanceFalseNegativeError',
                      'SNR',
                      'PSNR',
                      'SSIM',
                      ]


class MetricBase(object):
    _value_mask_exclude = -1
    _is_airway_metric = False
    _is_use_voxelsize = False
    _max_size_memory_safe = 5e+08

    def __init__(self, is_mask_exclude: bool = False) -> None:
        self._is_mask_exclude = is_mask_exclude
        self._name_fun_out = None

    def compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        if self._is_mask_exclude:
            return self._compute_masked(target.flatten(), input.flatten())
        else:
            return self._compute(target.flatten(), input.flatten())

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def _compute_masked(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return self._compute(self._get_masked_input(target, target),
                             self._get_masked_input(input, target))

    def _get_mask(self, target: np.ndarray) -> np.ndarray:
        return np.where(target == self._value_mask_exclude, 0, 1)

    def _get_masked_input(self, input: np.ndarray, target: np.ndarray) -> np.ndarray:
        return np.where(target == self._value_mask_exclude, 0, input)

    def compute_safememory(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        if (target.size > self._max_size_memory_safe):
            # if arrays are too large, split then in two and compute metrics twice, and return size-weighted metrics
            totaldim_0 = target.shape[0]
            metrics_1 = self.compute(target[0:totaldim_0 / 2], input[:totaldim_0 / 2])
            metrics_2 = self.compute(target[totaldim_0 / 2:], input[totaldim_0 / 2:])
            size_1 = target[0:totaldim_0 / 2].size
            size_2 = target[totaldim_0 / 2:].size
            return (metrics_1 * size_1 + metrics_2 * size_2) / (size_1 + size_2)
        else:
            return self.compute(target, input)


class CombineTwoMetrics(MetricBase):

    def __init__(self, metrics_1: MetricBase, metrics_2: MetricBase, weight_metric2over1: float = 1.0) -> None:
        super(CombineTwoMetrics, self).__init__(False)
        self._metrics_1 = metrics_1
        self._metrics_2 = metrics_2
        self._weight_metric2over1 = weight_metric2over1
        self._name_fun_out = '_'.join(['combi', metrics_1._name_fun_out, metrics_2._name_fun_out])

    def compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return self._metrics_1.compute(target, input) \
            + self._weight_metric2over1 * self._metrics_2.compute(target, input)

    def compute_safememory(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return self._metrics_1.compute_safememory(target, input) \
            + self._weight_metric2over1 * self._metrics_2.compute_safememory(target, input)


class MeanSquaredError(MetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(MeanSquaredError, self).__init__(is_mask_exclude)
        self._name_fun_out = 'mean_squared'

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return np.mean(np.square(input - target))

    def _compute_masked(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        mask = self._get_mask(target)
        return np.mean(np.square(input - target) * mask)


class MeanSquaredErrorLogarithmic(MetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(MeanSquaredErrorLogarithmic, self).__init__(is_mask_exclude)
        self._name_fun_out = 'mean_squared_log'

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return np.mean(np.square(np.log(np.clip(input, _EPS, None) + 1.0)
                                 - np.log(np.clip(target, _EPS, None) + 1.0)))

    def _compute_masked(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        mask = self._get_mask(target)
        return np.mean(np.square(np.log(np.clip(input, _EPS, None) + 1.0)
                                 - np.log(np.clip(target, _EPS, None) + 1.0)) * mask)


class BinaryCrossEntropy(MetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(BinaryCrossEntropy, self).__init__(is_mask_exclude)
        self._name_fun_out = 'bin_cross'

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return np.mean(- target * np.log(input + _EPS)
                       - (1.0 - target) * np.log(1.0 - input + _EPS))

    def _compute_masked(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        mask = self._get_mask(target)
        return np.mean((- target * np.log(input + _EPS)
                        - (1.0 - target) * np.log(1.0 - input + _EPS)) * mask)


class WeightedBinaryCrossEntropy(MetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(WeightedBinaryCrossEntropy, self).__init__(is_mask_exclude)
        self._name_fun_out = 'weight_bin_cross'

    def _get_weights(self, target: np.ndarray) -> Tuple[float, float]:
        num_class_1 = np.count_nonzero(target == 1)
        num_class_0 = np.count_nonzero(target == 0)
        return (1.0, num_class_0 / (float(num_class_1) + _EPS))

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        weights = self._get_weights(target)
        return np.mean(- weights[1] * target * np.log(input + _EPS)
                       - weights[0] * (1.0 - target) * np.log(1.0 - input + _EPS))

    def _compute_masked(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        weights = self._get_weights(target)
        mask = self._get_mask(target)
        return np.mean((- weights[1] * target * np.log(input + _EPS)
                        - weights[0] * (1.0 - target) * np.log(1.0 - input + _EPS)) * mask)


class WeightedBinaryCrossEntropyFixedWeights(WeightedBinaryCrossEntropy):
    weights_no_masks_exclude = (1.0, 80.0)
    weights_mask_exclude = (1.0, 300.0)  # for LUVAR data
    # weights_mask_exclude = (1.0, 361.0)  # for DLCST data

    def __init__(self, is_mask_exclude: bool = False) -> None:
        if is_mask_exclude:
            self._weights = self.weights_mask_exclude
        else:
            self._weights = self.weights_no_masks_exclude
        super(WeightedBinaryCrossEntropyFixedWeights, self).__init__(is_mask_exclude)
        self._name_fun_out = 'weight_bin_cross_fixed'

    def _get_weights(self, target: np.ndarray) -> Tuple[float, float]:
        return self._weights


class BinaryCrossEntropyFocalLoss(MetricBase):
    # Binary cross entropy + Focal loss
    _gamma_default = 2.0

    def __init__(self, gamma: float = _gamma_default, is_mask_exclude: bool = False) -> None:
        self._gamma = gamma
        super(BinaryCrossEntropyFocalLoss, self).__init__(is_mask_exclude)
        self._name_fun_out = 'bin_cross_focal_loss'

    def _get_predprobs_classes(self, target: np.ndarray, input: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        prob_1 = np.where(target == 1.0, input, 1)
        prob_0 = np.where(target == 0.0, input, 0)
        return (prob_1, prob_0)

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return np.mean(- target * pow(1.0 - input, self._gamma) * np.log(input + _EPS)
                       - (1.0 - target) * pow(input, self._gamma) * np.log(1.0 - input + _EPS))

    def _compute_masked(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        mask = self._get_mask(target)
        return np.mean((- target * pow(1.0 - input, self._gamma) * np.log(input + _EPS)
                        - (1.0 - target) * pow(input, self._gamma) * np.log(1.0 - input + _EPS)) * mask)


class DiceCoefficient(MetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(DiceCoefficient, self).__init__(is_mask_exclude)
        self._name_fun_out = 'dice'

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return (2.0 * np.sum(target * input)) / (np.sum(target) + np.sum(input) + _SMOOTH)


class TruePositiveRate(MetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(TruePositiveRate, self).__init__(is_mask_exclude)
        self._name_fun_out = 'tp_rate'

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return np.sum(target * input) / (np.sum(target) + _SMOOTH)


class TrueNegativeRate(MetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(TrueNegativeRate, self).__init__(is_mask_exclude)
        self._name_fun_out = 'tn_rate'

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return np.sum((1.0 - target) * (1.0 - input)) / (np.sum((1.0 - target)) + _SMOOTH)


class FalsePositiveRate(MetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(FalsePositiveRate, self).__init__(is_mask_exclude)
        self._name_fun_out = 'fp_rate'

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return np.sum((1.0 - target) * input) / (np.sum((1.0 - target)) + _SMOOTH)


class FalseNegativeRate(MetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(FalseNegativeRate, self).__init__(is_mask_exclude)
        self._name_fun_out = 'fn_rate'

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return np.sum(target * (1.0 - input)) / (np.sum(target) + _SMOOTH)


# *****************************************
class AirwayMetricBase(MetricBase):
    _is_airway_metric = True
    _is_use_voxelsize = False

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(AirwayMetricBase, self).__init__(is_mask_exclude)

    def _compute_airs(self, target: np.ndarray, target_cenline: np.ndarray,
                      input: np.ndarray, input_cenline: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def compute_airs(self, target: np.ndarray, target_cenline: np.ndarray, input: np.ndarray,
                     input_cenline: np.ndarray) -> np.ndarray:
        return self._compute_airs(target, target_cenline, input, input_cenline)

    def set_voxel_size(self, voxel_size: np.ndarray) -> None:
        self._voxel_size = np.array(voxel_size)


class AirwayCompleteness(AirwayMetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(AirwayCompleteness, self).__init__(is_mask_exclude)
        self._name_fun_out = 'completeness'

    def _compute_airs(self, target: np.ndarray, target_cenline: np.ndarray, input: np.ndarray,
                      input_cenline: np.ndarray) -> np.ndarray:
        return np.sum(target_cenline * input) / (np.sum(target_cenline) + _SMOOTH)


class AirwayVolumeLeakage(AirwayMetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(AirwayVolumeLeakage, self).__init__(is_mask_exclude)
        self._name_fun_out = 'volume_leakage'

    def _compute_airs(self, target: np.ndarray, target_cenline: np.ndarray, input: np.ndarray,
                      input_cenline: np.ndarray) -> np.ndarray:
        return np.sum((1.0 - target) * input) / (np.sum(target) + _SMOOTH)


class AirwayCentrelineLeakage(AirwayMetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(AirwayCentrelineLeakage, self).__init__(is_mask_exclude)
        self._name_fun_out = 'cenline_leakage'

    def _compute_airs(self, target: np.ndarray, target_cenline: np.ndarray, input: np.ndarray,
                      input_cenline: np.ndarray) -> np.ndarray:
        return np.sum((1.0 - target) * input_cenline) / (np.sum(target_cenline) + _SMOOTH)


class AirwayTreeLength(AirwayMetricBase):
    _is_use_voxelsize = True

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(AirwayTreeLength, self).__init__(is_mask_exclude)
        self._name_fun_out = 'tree_length'

    def _get_voxel_length_unit(self) -> np.ndarray:
        return np.prod(self._voxel_size) ** (1.0 / len(self._voxel_size))

    def _compute_airs(self, target: np.ndarray, target_cenline: np.ndarray, input: np.ndarray,
                      input_cenline: np.ndarray) -> np.ndarray:
        return np.sum(target_cenline * input) * self._get_voxel_length_unit()


class AirwayCentrelineDistanceFalsePositiveError(AirwayMetricBase):
    _is_use_voxelsize = True

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(AirwayCentrelineDistanceFalsePositiveError, self).__init__(is_mask_exclude)
        self._name_fun_out = 'cenline_dist_fp_err'

    def _get_cenline_coords(self, input_cenline: np.ndarray) -> np.ndarray:
        return np.asarray(np.argwhere(input_cenline > 0)) * self._voxel_size

    def _compute_airs(self, target: np.ndarray, target_cenline: np.ndarray, input: np.ndarray,
                      input_cenline: np.ndarray) -> np.ndarray:
        target_coords = self._get_cenline_coords(target_cenline)
        input_coords = self._get_cenline_coords(input_cenline)
        dists = distance.cdist(input_coords, target_coords)
        return np.mean(np.min(dists, axis=1))


class AirwayCentrelineDistanceFalseNegativeError(AirwayMetricBase):
    _is_use_voxelsize = True

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(AirwayCentrelineDistanceFalseNegativeError, self).__init__(is_mask_exclude)
        self._name_fun_out = 'cenline_dist_fn_err'

    def _get_cenline_coords(self, input_cenline: np.ndarray) -> np.ndarray:
        return np.asarray(np.argwhere(input_cenline > 0)) * self._voxel_size

    def _compute_airs(self, target: np.ndarray, target_cenline: np.ndarray, input: np.ndarray,
                      input_cenline: np.ndarray) -> np.ndarray:
        target_coords = self._get_cenline_coords(target_cenline)
        input_coords = self._get_cenline_coords(input_cenline)
        dists = distance.cdist(input_coords, target_coords)
        return np.mean(np.min(dists, axis=0))


# ******************** METRICS USED IN MRI_ENHANCE METHOD ********************

class MetricModifiedBase(MetricBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(MetricModifiedBase, self).__init__(is_mask_exclude)

    def compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        if self._is_mask_exclude:
            return self._compute_masked(target, input)
        else:
            return self._compute(target, input)

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def _compute_masked(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return self._compute(self._get_masked_input(target, target),
                             self._get_masked_input(input, target))

    def _get_mask(self, target: np.ndarray) -> np.ndarray:
        return np.where(target == self._value_mask_exclude, 0, 1)

    def _get_masked_input(self, input: np.ndarray, target: np.ndarray) -> np.ndarray:
        return np.where(target == self._value_mask_exclude, 0, input)


# Signal-to-Noise ratio
class SNR(MetricModifiedBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(SNR, self).__init__(is_mask_exclude)
        self._name_fun_out = 'snr'

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        mean = np.mean(input.flatten())
        std = np.std(input.flatten())
        return mean / std
        # return signaltonoise(input, axis=None)


# Peak Signal-to-Noise ratio
class PSNR(MetricModifiedBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(PSNR, self).__init__(is_mask_exclude)
        self._name_fun_out = 'psnr'
        self._max_value = 255.0

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        mse = np.mean(np.square(input.flatten() - target.flatten()))
        if mse == 0.0:
            return 0.0
        else:
            return 20.0 * np.log10(self._max_value / np.sqrt(mse))


# SSIM: Structural Similarity Index
class SSIM(MetricModifiedBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(SSIM, self).__init__(is_mask_exclude)
        self._name_fun_out = 'ssim'

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        return ssim(target, input, data_range=255.0)


# SSIM HOMEMADE FOR TESTING
class SSIMHomemade(MetricModifiedBase):

    def __init__(self, is_mask_exclude: bool = False) -> None:
        super(SSIMHomemade, self).__init__(is_mask_exclude)
        self._name_fun_out = 'ssim_homemade'

    def _compute(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        cons_k1 = 0.01
        cons_k2 = 0.03
        range_l = 255.0
        cons_c1 = (cons_k1*range_l)**2
        cons_c2 = (cons_k2*range_l)**2
        target = target.flatten()
        input = input.flatten()
        mean_target = np.mean(target, axis=-1)
        mean_input = np.mean(input, axis=-1)
        std_target = np.sqrt(np.mean(np.square(target - mean_target), axis=-1))
        std_input = np.sqrt(np.mean(np.square(input - mean_input), axis=-1))
        std_target_input = np.mean((target - mean_target) * (input - mean_input), axis=-1)
        return (2*mean_target*mean_input + cons_c1) / (mean_target**2 + mean_input**2 + cons_c1) *\
               (2*std_target_input + cons_c2) / (std_target**2 + std_input**2 + cons_c2)

    def _compute_masked(self, target: np.ndarray, input: np.ndarray) -> np.ndarray:
        cons_k1 = 0.01
        cons_k2 = 0.03
        range_l = 255.0
        cons_c1 = (cons_k1*range_l)**2
        cons_c2 = (cons_k2*range_l)**2
        target = target.flatten()
        input = input.flatten()
        mask = self._get_mask(target)
        mean_target = np.mean(target * mask, axis=-1)
        mean_input = np.mean(input * mask, axis=-1)
        std_target = np.sqrt(np.mean(np.square(target - mean_target) * mask, axis=-1))
        std_input = np.sqrt(np.mean(np.square(input - mean_input) * mask, axis=-1))
        std_target_input = np.mean((target - mean_target) * (input - mean_input) * mask, axis=-1)
        return (2*mean_target*mean_input + cons_c1) / (mean_target**2 + mean_input**2 + cons_c1) *\
               (2*std_target_input + cons_c2) / (std_target**2 + std_input**2 + cons_c2)
