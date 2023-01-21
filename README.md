# sample_python_multiprocessing

A sample implementation for creating multiple child processes and performing distributed parallel processing.
This implementation will be useful for the case that there are a large number of tasks with a large amount of computation.

"Parent" submits the request of the task to the Request Queue and lets "Children" retrieve and handle the task in parallel, then receives the result of the task in the Response Queue.
At that time, the progress bar is displayed to visualize the progress.
Logs generated in "Children" are passed to "Parent" via the Message Queue, and "Parent" show (or store) them as usual.
