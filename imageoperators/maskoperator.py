
from typing import List
import numpy as np

from common.exceptionmanager import catch_error_exception


class MaskOperator(object):
    _value_mask_bin = 1
    _value_background = 0

    @classmethod
    def binarise(cls, in_image: np.ndarray) -> np.ndarray:
        return np.clip(in_image, cls._value_background, cls._value_mask_bin)  # convert to binary masks (0, 1)

    @classmethod
    def _check_binary_mask(cls, in_image: np.ndarray) -> bool:
        # check that only contains binary values (0, 1)
        values_found = np.unique(in_image)
        if len(values_found) == 2 and \
            values_found[0] == cls._value_background and \
            values_found[1] == cls._value_mask_bin:
            return True
        else:
            return False

    @classmethod
    def mask_exclude_regions(cls,
                             in_image: np.ndarray,
                             in_mask_image: np.ndarray,
                             value_mask_exclude: int = -1
                             ) -> np.ndarray:
        return np.where(in_mask_image == cls._value_background, value_mask_exclude, in_image)

    @classmethod
    def mask_exclude_regions_fillzero(cls,
                                      in_image: np.ndarray,
                                      in_mask_image: np.ndarray
                                      ) -> np.ndarray:
        return cls.multiply_two_masks(in_image, in_mask_image)

    @classmethod
    def merge_two_masks(cls,
                        in_image_1: np.ndarray,
                        in_image_2: np.ndarray,
                        isnot_intersect_masks: bool = False
                        ) -> np.ndarray:
        if isnot_intersect_masks:
            # check there is no overlap between the two masks
            intersect_masks = np.multiply(in_image_1, in_image_2)

            indexes_intersect_masks = np.where(intersect_masks == cls._value_mask_bin)
            if len(indexes_intersect_masks[0] != 0):
                message = 'MaskOperator:merge_two_masks: Found intersection between the two input masks'
                catch_error_exception(message)

        out_image = in_image_1 + in_image_2
        return cls.binarise(out_image)

    @classmethod
    def substract_two_masks(cls, in_image_1: np.ndarray, in_image_2: np.ndarray) -> np.ndarray:
        out_image = (in_image_1 - in_image_2).astype(np.int8)
        return cls.binarise(out_image).astype(in_image_1.dtype)

    @classmethod
    def multiply_two_masks(cls, in_image_1: np.ndarray, in_image_2: np.ndarray) -> np.ndarray:
        out_image = np.multiply(in_image_1, in_image_2)
        return cls.binarise(out_image)

    @classmethod
    def get_masks_with_label(cls, in_image: np.ndarray, in_label: int) -> np.ndarray:
        return np.where(np.isin(in_image, in_label), cls._value_mask_bin, cls._value_background).astype(in_image.dtype)

    @classmethod
    def get_masks_with_labels_list(cls, in_image: np.ndarray, inlist_labels: List[int]) -> np.ndarray:
        return np.where(np.isin(in_image, inlist_labels), cls._value_mask_bin, cls._value_background).astype(in_image.dtype)

    @classmethod
    def get_list_masks_with_labels_list(cls, in_image: np.ndarray, inlist_labels: List[int]) -> List[np.ndarray]:
        return [cls.get_masks_with_label(in_image, ilabel) for ilabel in inlist_labels]

    @classmethod
    def get_list_masks_all_labels(cls, in_image: np.ndarray) -> List[np.ndarray]:
        inlist_labels = cls.extract_labels_in_masks(in_image)
        return cls.get_list_masks_with_labels_list(in_image, inlist_labels)

    @classmethod
    def extract_labels_in_masks(cls, in_image: np.ndarray) -> List[int]:
        return list(np.delete(np.unique(in_image), cls._value_background))