import torch
from torch import Tensor
from torch.nn import Module, Parameter
import torch.nn.functional as F

class BayesPReLUIMP(Module):
    r"""Applies the element-wise function:

    .. math::
        \text{PReLU}(x) = \max(0,x) + a * \min(0,x)

    or

    .. math::
        \text{PReLU}(x) =
        \begin{cases}
        x, & \text{ if } x \geq 0 \\
        ax, & \text{ otherwise }
        \end{cases}

    Here :math:`a` is a learnable parameter. When called without arguments, `nn.PReLU()` uses a single
    parameter :math:`a` across all input channels. If called with `nn.PReLU(nChannels)`,
    a separate :math:`a` is used for each input channel.


    .. note::
        weight decay should not be used when learning :math:`a` for good performance.

    .. note::
        Channel dim is the 2nd dim of input. When input has dims < 2, then there is
        no channel dim and the number of channels = 1.

    Args:
        num_parameters (int): number of :math:`a` to learn.
            Although it takes an int as input, there is only two values are legitimate:
            1, or the number of channels at input. Default: 1
        init (float): the initial value of :math:`a`. Default: 0.25

    Shape:
        - Input: :math:`(N, *)` where `*` means, any number of additional
          dimensions
        - Output: :math:`(N, *)`, same shape as the input

    Attributes:
        weight (Tensor): the learnable weights of shape (:attr:`num_parameters`).

    .. image:: ../scripts/activation_images/PReLU.png

    Examples::

        >>> m = nn.PReLU()
        >>> input = torch.randn(2)
        >>> output = m(input)
    """
    __constants__ = ['num_parameters', 'num_mc_samples']
    num_parameters: int
    num_mc_samples: int

    def __init__(self, num_parameters: int = 1, num_mc_samples: int = 20, init: float = 0.25) -> None:
        super(BayesPReLUIMP, self).__init__()
        self.num_parameters = num_parameters
        self.mc_sample_id = None
        self.num_mc_samples = num_mc_samples
        self.parallel_eval = False

        self.weights = Parameter(torch.Tensor(num_mc_samples, num_parameters).fill_(init))

    def forward(self, input: Tensor) -> Tensor:
        assert False
        if self.parallel_eval:
            return torch.maximum(input, 0) + self.weights[None, :, :, None, None] * torch.minimum(input, 0)
        elif isinstance(self.mc_sample_id, int):
            self.mc_sample_id = self.mc_sample_id % self.num_mc_samples
            weight = self.weights[self.mc_sample_id]
            return F.prelu(input, weight)
        else:
            idx = torch.tensor(self.mc_sample_id, device=input.device, dtype=torch.long)
            weight = self.weights[idx]
            return torch.maximum(input, 0) + weight[:, :, None, None] * torch.minimum(input, 0)

    def extra_repr(self) -> str:
        return 'num_parameters={}, num_mc_samples={}'.format(self.num_parameters, self.num_mc_samples)
