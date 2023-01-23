.. sample-python-multiprocessing documentation master file, created by
   sphinx-quickstart on Tue Jan 24 05:02:07 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to sample-python-multiprocessing's documentation!
=========================================================

A sample implementation for creating multiple child processes
and performing distributed parallel processing.
This implementation will be useful for the case that
there are a large number of tasks with a large amount of computation.

Assuming that preparing resources to handle a task is a very heavy process,
Instead of creating a child process for each task and throwing it away,
Spawns a small number of child processes compared to the number of tasks,
Reusing that limited number of child processes to handle multiple tasks
(e.g. load Machile Learning model in child process
to making predictions on the data).
To control tasks and child processes, I implemented using Queues.

The Parent class submits the request of the task to the Request Queue
and lets the Child processes retrieve and handle the task in parallel,
then receives the result of the task in the Response Queue.

At that time, the progress bar is displayed to visualize the progress.
Logs generated in Child processes are passed to the Parent class
via the Message Queue, and the Parent class show (or store) them as usual.

複数の子プロセスを生成し、分散並列処理をするサンプル実装。
多くの計算量を要する多数のタスクを処理する場合に参考になると思う。

タスクを処理するための資源を用意することが非常に重い処理である場合を想定し、
タスク毎に子プロセスを生成して使い捨てるのではなく、
タスク数と比較して少数の子プロセスを生成し、
その限られた数の子プロセスを使い回して複数のタスクを処理させている
（例えば子プロセスで Machile Learning model をロードして
データの予測を行う場合など）。
このタスクと子プロセスの制御のために、Queue を使って実装している。

親プロセスはタスクを Request Queue に登録し、
それを複数の子プロセスに受け取らせて処理を行わせ、
Response Queue でその処理結果を受け取る。

それと同時に、その進捗状況を Progress Bar で可視化する。
また子プロセスで発生したログは Message Queue を介し
親プロセスが受け取り、それらログを通常のログと同様に処理する。

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   src

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
