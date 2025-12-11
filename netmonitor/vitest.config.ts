import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Limit parallel workers to prevent resource exhaustion
    maxWorkers: 2,
    minWorkers: 1,

    // Use 'forks' pool for better process isolation and cleanup
    pool: 'forks',

    // Disable file-level parallelism for more predictable resource usage
    fileParallelism: false,
  },
});
