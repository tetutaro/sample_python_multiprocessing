# sample_python_multiprocessing

A sample implementation for creating multiple child processes and performing distributed parallel processing.
This implementation will be useful for the case that there are a large number of tasks with a large amount of computation.

"Parent" submits the request of the task to the Request Queue and lets "Children" retrieve and handle the task in parallel, then receives the result of the task in the Response Queue.
At that time, the progress bar is displayed to visualize the progress.
Logs generated in "Children" are passed to "Parent" via the Message Queue, and "Parent" show (or store) them as usual.

## How to run the program

invoke the command on your terminal `python run.py` or `make run`.

```
usage: run.py [-h] [-n NCHILD]

A sample implementation of multiprocessing

options:
  -h, --help                    show this help message and exit
  -n NCHILD, --nchild NCHILD    the number of child processes
                                (defualt: -1 == os.cpu_count() - 1)
```

if you use, you can indicate the option like `make run NCHILD=8`.
