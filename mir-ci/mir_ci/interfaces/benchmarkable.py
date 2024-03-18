from abc import ABC, abstractmethod

from ..lib.cgroups import Cgroup


class Benchmarkable(ABC):
    @abstractmethod
    async def get_cgroup(self) -> Cgroup:
        raise NotImplementedError

    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, *args):
        raise NotImplementedError
