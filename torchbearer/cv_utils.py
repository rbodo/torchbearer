import math

import torch
from torch.utils.data import TensorDataset, Dataset
import random


def train_valid_splitter(x, y, split, shuffle=True):
    """ Generate training and validation tensors from whole dataset data and label tensors

    Args:
        x (:class:`torch.Tensor`): Data tensor for whole dataset
        y (:class:`torch.Tensor`): Label tensor for whole dataset
        split (float): Fraction of dataset to be used for validation
        shuffle (bool): If True randomize tensor order before splitting else do not randomize

    Returns:
        Training and validation tensors (training data, training labels, validation data, validation labels)
    """
    num_samples_x = x.size()[0]
    num_valid_samples = int(math.floor(num_samples_x * split))

    if shuffle:
        indicies = torch.randperm(num_samples_x)
        x, y = x[indicies], y[indicies]

    x_val, y_val = x[:num_valid_samples], y[:num_valid_samples]
    x, y = x[num_valid_samples:], y[num_valid_samples:]

    return x, y, x_val, y_val


def get_train_valid_sets(x, y, validation_data, validation_split, shuffle=True):
    """ Generate validation and training datasets from whole dataset tensors

    Args:
        x (:class:`torch.Tensor`): Data tensor for dataset
        y (:class:`torch.Tensor`): Label tensor for dataset
        validation_data ((:class:`torch.Tensor`, :class:`torch.Tensor`)): Optional validation data (x_val, y_val) to be
            used instead of splitting x and y tensors
        validation_split (float): Fraction of dataset to be used for validation
        shuffle (bool): If True randomize tensor order before splitting else do not randomize

    Returns:
        Training and validation datasets
    """

    valset = None

    if validation_data is not None:
        x_val, y_val = validation_data
    elif isinstance(validation_split, float):
        x, y, x_val, y_val = train_valid_splitter(x, y, validation_split, shuffle=shuffle)
    else:
        x_val, y_val = None, None

    trainset = TensorDataset(x, y)
    if x_val is not None and y_val is not None:
        valset = TensorDataset(x_val, y_val)

    return trainset, valset


class DatasetValidationSplitter:
    def __init__(self, dataset_len, split_fraction, shuffle_seed=None):
        """ Generates training and validation split indicies for a given dataset length and creates training and
        validation datasets using these splits

        Args:
            dataset_len (int): The length of the dataset to be split into training and validation
            split_fraction (float): The fraction of the whole dataset to be used for validation
            shuffle_seed: Optional random seed for the shuffling process. See `random.seed <https://docs.python.org/2/library/random.html#random.seed>`_
        """
        self.dataset_len = dataset_len
        self.split_fraction = split_fraction
        self.valid_ids = None
        self.train_ids = None
        self._gen_split_ids(shuffle_seed)

    def _gen_split_ids(self, seed):
        all_ids = list(range(self.dataset_len))

        if seed is not None:
            random.seed(seed)
        random.shuffle(all_ids)

        num_valid_ids = int(math.floor(self.dataset_len*self.split_fraction))
        self.valid_ids = all_ids[:num_valid_ids]
        self.train_ids = all_ids[num_valid_ids:]

    def get_train_dataset(self, dataset):
        """ Creates a training dataset from existing dataset

        Args:
            dataset (:class:`torch.utils.data.Dataset`): Dataset to be split into a training dataset

        Returns:
            :class:`torch.utils.data.Dataset`: Training dataset split from whole dataset
        """
        return SubsetDataset(dataset, self.train_ids)

    def get_val_dataset(self, dataset):
        """ Creates a validation dataset from existing dataset

        Args:
        dataset (:class:`torch.utils.data.Dataset`): Dataset to be split into a validation dataset

        Returns:
            :class:`torch.utils.data.Dataset`: Validation dataset split from whole dataset
        """
        return SubsetDataset(dataset, self.valid_ids)

    def get_sets(self, dataset):
        """ Gets a training and validation set tuple

        Args:
            dataset (:class:`torch.utils.data.Dataset`): Dataset to be split into a training and validation datasets

        Returns:
            tuple (:class:`torch.utils.data.Dataset`): Tuple of returned training and val datasets
        """
        return self.get_train_dataset(dataset), self.get_val_dataset(dataset)

    def state_dict(self):
        """
        Returns: state dict containing dataset ids
        """
        return {'train_ids': self.train_ids, 'valid_ids': self.valid_ids}

    def load_state_dict(self, state_dict):
        """ Loads a state dict so that previously generated dataset splits can be reused

        Args:
            state_dict: state dictionary

        """
        self.train_ids, self.valid_ids = state_dict['train_ids'], state_dict['valid_ids']


class SubsetDataset(Dataset):
    def __init__(self, dataset, ids):
        """ Dataset that consists of a subset of a previous dataset

        Args:
            dataset (:class:`torch.utils.data.Dataset`): Complete dataset
            ids (list): List of subset IDs
        """
        super(SubsetDataset, self).__init__()
        self.dataset = dataset
        self.ids = ids

    def __getitem__(self, index):
        return self.dataset.__getitem__(self.ids[index])

    def __len__(self):
        return len(self.ids)
