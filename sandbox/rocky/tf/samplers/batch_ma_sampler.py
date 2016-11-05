from rllab.sampler.base import BaseSampler
from rllab.sampler import parallel_sampler, ma_sampler
from rllab.sampler.stateful_pool import singleton_pool
import tensorflow as tf


class BatchMASampler(BaseSampler):

    def start_worker(self):
        if singleton_pool.n_parallel > 1:
            singleton_pool.run_each(worker_init_tf)
        if hasattr(self.algo, 'policies'):
            parallel_sampler.populate_task(self.algo.env, self.algo.policies)
        else:
            parallel_sampler.populate_task(self.algo.env, self.algo.policy)
        if singleton_pool.n_parallel > 1:
            singleton_pool.run_each(worker_init_tf_vars)

    def shutdown_worker(self):
        ma_sampler.terminate_task(scope=self.algo.scope)

    def obtain_samples(self, itr):
        cur_policy_params = self.algo.policy.get_param_values()
        if hasattr(self.algo.env, "get_param_values"):
            cur_env_params = self.algo.env.get_param_values()
        else:
            cur_env_params = None
            paths = ma_sampler.sample_paths(
                policy_params=cur_policy_params,
                env_params=cur_env_params,
                max_samples=self.algo.batch_size,
                max_path_length=self.algo.max_path_length,
                ma_mode=self.algo.ma_mode,
                scope=self.algo.scope,)
        if self.algo.whole_paths:
            return paths
        else:
            paths_truncated = parallel_sampler.truncate_paths(paths, self.algo.batch_size)
            return paths_truncated
