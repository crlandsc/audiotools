from typing import List

from torch import nn

from .. import AudioSignal
from .. import STFTParams


class MultiScaleSTFTLoss(nn.Module):
    """
    Computes the multi-scale STFT loss from [1].
    [1] Differentiable Digital Signal Processing
    """

    def __init__(
        self,
        window_lengths: List[int] = [2048, 512],
        loss_fn=nn.L1Loss(),
        clamp_eps: float = 1e-5,
        mag_weight: float = 1.0,
        log_weight: float = 1.0,
    ):
        super().__init__()
        self.stft_params = [
            STFTParams(window_length=w, hop_length=w // 4) for w in window_lengths
        ]
        self.loss_fn = loss_fn
        self.log_weight = log_weight
        self.mag_weight = mag_weight
        self.clamp_eps = clamp_eps

    def forward(self, x: AudioSignal, y: AudioSignal):
        loss = 0.0
        for s in self.stft_params:
            x.stft(s.window_length, s.hop_length, s.window_type)
            y.stft(s.window_length, s.hop_length, s.window_type)
            loss += self.log_weight * self.loss_fn(
                x.magnitude.pow(2).clamp(self.clamp_eps).log10(),
                y.magnitude.pow(2).clamp(self.clamp_eps).log10(),
            )
            loss += self.mag_weight * self.loss_fn(x.magnitude, y.magnitude)
        return loss


class MelSpectrogramLoss(nn.Module):
    """Compute distance between mel spectrograms."""

    def __init__(
        self,
        n_mels: List[int] = [150, 80],
        window_lengths: List[int] = [2048, 512],
        loss_fn=nn.L1Loss(),
        clamp_eps: float = 1e-5,
        mag_weight: float = 1.0,
        log_weight: float = 1.0,
    ):
        super().__init__()
        self.stft_params = [
            STFTParams(window_length=w, hop_length=w // 4) for w in window_lengths
        ]
        self.n_mels = n_mels
        self.loss_fn = loss_fn
        self.clamp_eps = clamp_eps
        self.log_weight = log_weight
        self.mag_weight = mag_weight

    def forward(self, x: AudioSignal, y: AudioSignal):
        loss = 0.0
        for n_mels, s in zip(self.n_mels, self.stft_params):
            kwargs = {
                "window_length": s.window_length,
                "hop_length": s.hop_length,
                "window_type": s.window_type,
            }
            x_mels = x.mel_spectrogram(n_mels, **kwargs)
            y_mels = y.mel_spectrogram(n_mels, **kwargs)

            loss += self.log_weight * self.loss_fn(
                x_mels.pow(2).clamp(self.clamp_eps).log10(),
                y_mels.pow(2).clamp(self.clamp_eps).log10(),
            )
            loss += self.mag_weight * self.loss_fn(x_mels, y_mels)
        return loss