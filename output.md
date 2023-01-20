# 0. SUMMARY

In the theory of real-time scheduling, tasks are described by mathematical variables, which are used in analytical models in order to prove schedulability of the system. On real-time Linux, tasks are computer programs, and Linux developers try to lower the latencies caused by the Linux kernel, trying to achieve faster response for the highest-priority task. Although both seek temporal correctness, they use different abstractions, which end up separating these efforts in two different worlds, making it hard for the Linux practitioners to understand and apply the formally proved models to the Linux kernel and for theoretical researchers to apply the restrictions imposed by Linux for the theoretical models. This paper traces a parallel between the theory of response-time analysis and the abstractions used in the Linux kernel. The contribution of this paper is threefold. We first identify the PREEMPT RT Linux kernel mechanisms that impact the timing of real-time tasks and map these impacts to the main abstractions used by the real-time scheduling theory. Then, we describe a customized trace tool, based on the existing trace infrastructure of the Linux kernel, that allows the measurement of the delays associated with the main abstractions of the real-time scheduling theory. Finally, we use this customized trace tool to characterize the timing lines resulting from the behavior of the PREEMPT RT Linux kernel.

> 在实时调度理论中，任务由数学变量描述，这些变量用于分析模型，以证明系统的调度性。在实时 Linux 上，任务是计算机程序，Linux 开发人员试图降低由 Linux 内核引起的潜伏期，以实现最高优先级任务的更快响应。尽管两者都寻求时间正确，但他们使用不同的抽象，最终将这些努力分开在两个不同的世界中，这使 Linux 从业者很难理解并将正式证明的模型应用于 Linux 内核，并使理论研究人员适用于实施的限制。由 Linux 用于理论模型。本文追踪响应时间分析理论和 Linux 内核中使用的抽象之间的相似之处。本文的贡献分为 3 部分。
> 我们首先确定影响实时任务时机的 RT Linux 内核机制，并将这些影响映射到实时调度理论所使用的主要抽象。然后，我们根据 Linux 内核的现有跟踪基础架构来描述一种定制的痕量工具，该工具允许测量与实时调度理论的主要抽象相关的延迟。最后，我们使用此自定义的跟踪工具来表征由 RT Linux 内核行为产生的定时线。

KEY WORDS: real time; response-time analysis; Linux; PREEMPT RT; trace; Ftrace

> 关键词：实时；响应时间分析；Linux;抢占 RT；痕迹;ftrace

# 1. INTRODUCTION

In recent years, Linux has gained several characteristics of a real-time operating system, and it has been used as such in both production systems [1](#_bookmark32), [2](#_bookmark33) and research projects [3](#_bookmark34), [4](#_bookmark35). Various realtime features have been added to the Linux kernel by several different groups. Some of them seek greater predictability for the kernel execution, as is the case of the project PREEMPT RT [5](#_bookmark36), which is an initiative of the kernel developers. Others implement real-time scheduling algorithms and mutual exclusion policies in the Linux kernel, as is the case of projects imus$RT$ [3](#_bookmark34) and SCHED_DEADLINE [4](#_bookmark35), which are both initiatives of the academic world. These initiatives were responsible for giving Linux both the ability to meet timing requirements such as tight response times [6](#_bookmark37) and the capacity of scheduling tasks using state-of-the-art algorithms from the real-time scheduling theory [7](#_bookmark38), [8](#_bookmark39).

> 近年来，Linux 已获得了实时操作系统的几个特征，并且在生产系统[1](#_ bookmark32)，[2](#_ bookmark33)和研究项目中都已使用。＃_Bookmark34)，[4](#_ bookmark35)。几个不同的组已将各种实时功能添加到 Linux 内核中。他们中的一些人对内核执行寻求更大的可预测性，就像项目抢占 RT [5](#_ bookmark36)的情况一样，这是内核开发人员的倡议。其他人则在 Linux 内核中实施实时调度算法和相互排除策略，就像项目 Imus $ rt $ [3](#_ bookmark34)和 Sched*deadline [4](#* bookmark35)一样世界。这些举措负责赋予 Linux 满足时间要求的能力，例如紧密响应时间[6](#_ bookmark37)，以及使用实时调度理论中最先进的算法进行调度任务的能力[7](#_ bookmark38)，[8](#\_ bookmark39)。

The goal of the developers from the industry and the researchers from the academia is the same: to transform Linux into a real-time operating system. But there are conceptual differences that end up distancing the developments of academia and industry. These differences are reported both by the developers of Linux [9](#_bookmark40) and by researchers [10](#_bookmark41). These differences arise in part because both communities use different abstractions for the system components and different system validation methods.

> 该行业的开发人员和学术界的研究人员的目标是相同的：将 Linux 转变为实时操作系统。但是，概念上的差异最终使学术界和行业的发展疏远了。Linux [9](#_ bookmark40)的开发人员和研究人员[10](#_ bookmark41)报告了这些差异。这些差异之所以出现，部分是因为两个社区对系统组件和不同的系统验证方法都使用不同的抽象。

In the context of the Linux operating system, tasks are parts of computer programs with timing constraints and properties. The task concept used in the real-time scheduling theory usually corresponds to just a portion of all operating system tasks. Some of these constraints are specified by the application, such as the period of the execution of a certain function, and some properties are estimated, such as the time necessary to finish a certain function. The main objective of developing the PREEMPT RT patch was to start a task with the least possible delay [11](#_bookmark42), which is usually called system latency. The system latency measures the ability of the operating system to give control to the highest-priority task as quickly as possible [10](#_bookmark41). This objective is achieved through reducing the number and size of points where the system remains with interrupts and preemption disabled.

> 在 Linux 操作系统的上下文中，任务是具有正时约束和属性的计算机程序的一部分。实时调度理论中使用的任务概念通常仅对应于所有操作系统任务的一部分。这些约束中的一些是由应用程序指定的，例如执行某个函数的周期，并估算了某些属性，例如完成特定功能所需的时间。开发抢先 RT 补丁的主要目标是以最小可能的延迟[11](#_ bookmark42)启动任务，该任务通常称为系统延迟。系统延迟衡量操作系统尽快控制最高优先级任务的能力[10](#_ bookmark41)。通过减少系统中断和预先抢先的点的点数和大小来实现此目标。

In the real-time scheduling theory, a system is modeled as a set of _n_ tasks _τ_ D ¹*τ$1$, τ$2$, . . . , τ$n$*º, and each task has its timing behavior defined by a set of variables, such as its period _P_ , worstcase execution time _S_ , and relative deadline _D_. These tasks are scheduled on a set of _m_ processors _p_ D ¹*p$1$, p$2$, . . . , p$m$*º, and they may share _q_ resources _ơ_ D ¹*ơ$1$, ơ$2$, . . . , ơ$q$*º, which require mutual exclusion. In this context, the main goal of the analysis is to somehow assign time of processors from _p_ and resources from _ơ_ to tasks from _τ_ in order to finish all tasks from _τ_ while meeting the timing constraints of each task [12](#_bookmark43).

> 在实时调度理论中，将一个系统建模为一组 _n_ 任务 _τ_d2τ$ 1 $，τ$ 2 $，。。。，τ$ n $\*º，每个任务都有其定时行为由一组变量定义，例如其周期\_p_，糟糕的执行时间 _s_ 和相对截止日期 _d_。这些任务安排在一组 _m_ 处理器 _p_ d 2*p $ 1 $，p $ 2 $，。。。，p $ m $*º，他们可以共享* q* resources*ơ_d 2*$ 1 $，ơ$ 2 $，。。。，ơ$ q $*°，需要相互排除。在这种情况下，分析的主要目标是以某种方式分配从\_p*分配处理器的时间，从 _ơ_ 分配了从 _τ_ 到任务的资源，以便从 _τ_ 完成所有任务，同时满足每个任务的定时约束[12](#\_ bookmark43)。

There would be important gains from the better integration between the real-time scheduling theory and the real-time Linux. For example, response-time analysis is a classical method used in the schedulability analysis of fixed-priority real-time systems [13](#_bookmark44), which is the case of Linux with the PREEMPT RT patch. By using the response-time analysis, it would be possible in principle to determine whether a task set is schedulable or not, provided that the worst-case execution times are known. The real-time scheduling theory allows analyses that go far beyond the simple latency measurement usually used as the main concern of the real-time Linux community.

> 实时调度理论和实时 Linux 之间的更好整合将带来重要的收益。例如，响应时间分析是一种经典方法，用于固定优先实时系统的调度性分析[13](#\_ bookmark44)，这就是 Linux 带有 prement RT 补丁的情况。通过使用响应时间分析，只要知道最坏的执行时间，就可以原则上确定任务集是否可计划。实时调度理论允许进行分析，这些分析远远超出了通常用作实时 Linux 社区的主要关注点的简单延迟测量。

The reason why the real-time scheduling theory is not used in the context of real-time Linux is that the task models used in the scheduling theory are usually too simple, and their set of constraints and task dependencies among tasks does not reproduce the reality of real-time applications running on a Linux kernel. Despite the vast literature on real-time scheduling, few of these results are to be used by the Linux development community [9](#_bookmark40).

> 实时调度理论在实时 Linux 的上下文中不使用实时调度理论的原因是，调度理论中使用的任务模型通常太简单了，并且任务之间的一系列约束和任务依赖性集也不会重现现实在 Linux 内核上运行的实时应用程序。尽管有关于实时时间表的大量文献，但 Linux 开发社区[9](#\_ bookmark40)很少使用这些结果。

In this context, the contribution of this paper is threefold. We first identify PREEMPT RT Linux kernel mechanisms that impact the timing of real-time tasks and map these impacts to the main abstractions used by the real-time scheduling theory. Then, we describe a customized trace tool, based on the existing trace infrastructure of the Linux kernel, that allows the measurement of the delays associated with the main abstractions of the real-time scheduling theory. Finally, we use this customized trace tool to characterize the timing lines resulting from the behavior of the PREEMPT RT Linux kernel. We believe this characterization is an important step in the direction of creating correct task models of the PREEMPT RT Linux and development of analytical methods for its schedulability analysis.

> 在这种情况下，本文的贡献是三倍。我们首先确定了影响实时任务时机的抢占 RT Linux 内核机制，并将这些影响映射到实时调度理论所使用的主要抽象。然后，我们根据 Linux 内核的现有跟踪基础架构来描述一种定制的痕量工具，该工具允许测量与实时调度理论的主要抽象相关的延迟。最后，我们使用此自定义的跟踪工具来表征由 RT Linux 内核行为产生的定时线。我们认为，这种表征是在创建 Preement RT Linux 的正确任务模型的方向上的重要一步，并开发了分析方法以进行计划分析。

In this paper, we go beyond the simple measurement of latency, which is usually found in papers on real-time Linux. We identify the mechanisms of the PREEMPT RT Linux kernel that affect the timing of the tasks and how the tasks affect each other, through these mechanisms. With this, it is possible to list important aspects of the PREEMPT RT Linux where improvement is possible, regarding the response time of high-priority tasks and not just the latency.

> 在本文中，我们超越了对潜伏期的简单测量，这通常在实时 Linux 的论文中找到。我们通过这些机制确定了影响任务时机以及任务如何相互影响的抢占 RT Linux 内核的机制。这样，就可以在高优先级任务的响应时间而不仅仅是延迟的响应时间方面列出可以改进的先发制人 RT Linux 的重要方面。

Also, by observing the Linux from the perspective of the real-time scheduling theory, we can better understand the constraints that currently exist in the PREEMPT RT Linux kernel and contribute towards the development of new task models based on these constraints. This is a necessary step to be able to develop appropriate schedulability tests in the future.

> 同样，通过从实时调度理论的角度观察 Linux，我们可以更好地理解当前在 RT Linux 内核中存在的约束，并根据这些约束来开发新任务模型。这是能够在将来开发适当的可计划测试的必要步骤。

The customized trace tool has also been proved very useful for analyzing the timeline of the execution of tasks on Linux. It can be used, for instance, by advanced users of Linux systems that require low latency to discover the source of the largest delays. It can assist them in the setup process, the fine tuning of the system, and the verification of new algorithms implemented in the kernel. It can also be used by researchers to understand the cause of high latency values, which sometimes cannot be explained and are just tagged as outliers.

> 也已证明自定义的跟踪工具对于分析 Linux 上执行任务的时间表非常有用。例如，Linux 系统的高级用户可以使用它，这些系统需要低延迟才能发现最大延迟的来源。它可以帮助他们进行设置过程，系统的微调以及内核中实现的新算法的验证。研究人员也可以使用它来理解高潜伏期值的原因，有时无法解释，仅将其标记为离群值。

We believe that a better integration between academia and the developers and users of PREEMPT RT Linux is important because of the vast potential of use of this platform in supporting real-time applications. This integration will help Linux users to find the sources of latencies in their real-time applications, Linux developers to understand the abstractions used in the scheduling theory and identify them within the Linux code, and the theoretical researchers to understand the realities of the PREEMPT RT Linux kernel and create more appropriate task models and schedulability analyses for this context.

> 我们认为，学术界与抢先 RT Linux 的开发人员和用户之间的更好集成非常重要，因为使用该平台在支持实时应用程序中具有巨大的潜力。该集成将帮助 Linux 用户在其实时应用程序中找到潜伏期的来源，Linux 开发人员了解计划理论中使用的抽象并在 Linux 代码中识别它们，以及理论研究人员了解 preempt RT 的现实性 Linux 内核并为此上下文创建更合适的任务模型和计划分析。

Section [2](#_bookmark0) presents the abstractions used in the response-time analysis, followed by the mapping between these abstractions and the Linux kernel abstractions in Section [3](#_bookmark3). Section [4](#_bookmark11) presents the customized trace tool, which is used to characterize Linux timeline in Section [5](#_bookmark12). The characterization of Linux execution is used to measure the timing properties of Linux tasks in Section [6](#_bookmark18), and a study case of the execution of the highest-priority task is shown in Section [7](#_bookmark23). Finally, Section [8](#_bookmark31) has our final comments, along with suggestions of future work.

> [2](#_ Bookmark0)节介绍了响应时间分析中使用的抽象，然后在[3](#_ bookmark3)中进行这些抽象和 Linux 内核抽象之间的映射。[4](#_ Bookmark11)节介绍了定制的跟踪工具，该工具用于表征[5](#_ bookmark12)中的 Linux 时间轴。Linux 执行的表征用于测量[6](#_ bookmark18)中 Linux 任务的定时属性，并且在[7](#_ bookmark23)节中显示了执行最高优先级任务的研究案例。最后，[8](#\_ bookmark31)节有我们的最终评论，以及未来工作的建议。

# 2. ABSTRACTIONS OF RESPONSE-TIME ANALYSIS

> ＃2.响应时间分析的抽象

The main objective of this section is to introduce the abstractions and mathematical variables used

> 本节的主要目的是介绍所使用的抽象和数学变量

by the response-time analysis, for subsequent mapping of these abstractions to the functions and

> 通过响应时间分析，将这些抽象映射到功能和

abstractions used in the Linux kernel.

> Linux 内核中使用的抽象。

In order to guarantee the timing correctness while executing real-time tasks, one has to know whether a given set of tasks and execution model will complete within their respective deadlines. There are several analytical methods to obtain this guarantee, depending on the execution model of the system. The Linux kernel is based on fixed priority, together with several mutual exclusion protocols. It is possible to verify the schedulability of a system that follows this model using the method of response-time analysis [14](#_bookmark45). Although the response-time method is only valid for uniprocessor systems, the choice to use this method was made for didactic purposes. Moreover it uses the common abstractions of the real-time literature.

> 为了确保执行实时任务时的时序正确性，必须知道给定的一组任务和执行模型是否会在其各自的截止日期内完成。根据系统的执行模型，有几种获得此保证的分析方法。Linux 内核基于固定优先级，以及几个相互排除方案。可以使用响应时间分析方法[14](#\_ bookmark45)验证遵循此模型的系统的计划性。尽管响应时间方法仅适用于单层系统系统，但选择使用此方法的选择是为教学目的。此外，它使用了实时文献的共同抽象。

According to the response-time analysis method, a system is composed of a set _τ_ of _n_ tasks, which in turn are described by a set of algebraic variables related to its timing behavior. Each variable represents an abstraction used in the method. These variables and the abstractions that they represent are the following:

> 根据响应时间分析方法，一个系统由 _n_ 任务的集合 _τ_ 组成，而该系统又由一组与其正时行为相关的代数变量来描述。每个变量代表该方法中使用的抽象。这些变量及其代表的抽象如下：

_C_ : the worst-case execution time;

> _c_：最差的执行时间；

_P_ : the period of activation;

> _p_：激活期；

_D_: the relative deadline;

> _d_：相对截止日期；

_J_ : the maximum release jitter;

> _j_：最大发行抖动；

_B_: the worst-case blocking time;

> _b_：最差的阻塞时间；

_I_ : the interference;

> _i_：干扰；

_W_ : the busy period; and

> _W_：繁忙的时期；和

_R_: the maximum response time.

> _r_：最大响应时间。

The worst-case execution time _S_ is the maximum computation time of the task. The period _P_ is the activation period of a periodic task, and _D_ denotes the relative deadline of the task. The release jitter, denoted by variable _J_ , is the delay at the beginning of the execution of a task, caused by a lower-priority task.

> 最差的执行时间 _s_ 是任务的最大计算时间。_p_ 期间是定期任务的激活期，_d_ 表示任务的相对截止日期。由变量 _J_ 表示的发行抖动是由较低优先级任务引起的任务执行开始时的延迟。

_B_ is the worst-case blocking time. A blocking happens when a higher-priority task has its execution delayed by a lower-priority task, generally because the lower-priority task holds some resources required by the higher-priority task. Generally, these resources are managed through a mutual exclusion mechanism.

> _b_ 是最糟糕的阻塞时间。当较高优先级任务的执行被较低优先级任务延迟时，就会发生阻碍，这通常是因为较低优先级任务保留了较高优先级任务所需的一些资源。通常，这些资源是通过相互排除机制来管理的。

Based on these variables, the response-time method is used to define the value of _I_ , _W_ , and _R_, for each task of the system. The interference _I$i$_ of a task _τ$i$_ is the sum of all computation time of tasks in the set _hp(i)_ that was activated during the busy period of task _i_ , where _hp(i)_ is the set of tasks with priorities higher than _τ$i$_ :

> 基于这些变量，响应时间方法用于为系统的每个任务定义 _i_，_w_ 和 _r_ 的值。干扰*i $ i $ *的任务* τ$ i $ *是集合* hp(i)*中所有计算时间的总和。优先级高于* τ$ i $ *：：：

`$$`

> $ $`

![](./media/image1.png)
<img src="./media/image8.png" style="width:0.32826in" />
<img src="./media/image9.png" style="width:0.3275in;height:0.13812in" />

Figure 1. <span id="_bookmark1" class="anchor"></span>Response-time analysis abstractions.

> 图 1. <span ID =“ \_ bookmark1” class =“锚”> </span>响应时间分析抽象。

The busy period _W$i$_ of a task _τ$i$_ corresponds to the sum of its computational time, blocking time, and interference. It is given by Equation ([2](#_bookmark2)).

> 任务的繁忙期*W $ i $ * *τ$ i $ *对应于其计算时间的总和，阻止时间和干扰。它由等式([2](#\_ bookmark2))给出。

`$$`

> $ $`

It is important to notice that _W$i$_ appears on both sides of the equation, because of its use on the definition of the interference. This dependence implies in the use of an iterative method to determine _W$i$_ . In this case, the initial value of _W$i$_ is the worst-case execution time _S$i$_ , and Equation ([2](#_bookmark2)) is used iteratively _x_ times, until _W $x_C*1$ D \_W $x$_ or \_W $x_C*1$ > D$i$\_ .

> 重要的是要注意*w $ i $ *出现在等式的两侧，因为它在干扰的定义上使用。这种依赖性意味着使用迭代方法来确定* W $ i $ *。在这种情况下，*w $ i $ *的初始值是最差的执行时间* s $ i $ *，而方程式([2](#_ bookmark2))被迭代\_x_ times，直到* w $ x_c\*1 $d \ \_w $ x $ *或\ _W $ x_c\*1 $> d $ i $ \ _。

`$$`

> $ $`

A system is said to be schedulable if for every task i , the maximum response time Ri is less than

> 据说如果对于每个任务 i，最大响应时间 ri 小于

or equal to its deadline Di .

> 或等于其截止日期。

## 2.1. Graphical representation of response-time analysis abstractions\_

> ## 2.1。响应时间分析的图形表示抽象\ \_

A common way to represent the behavior of a real-time task is using a graphical format. Figure [1](#_bookmark1) shows how each abstraction used in the response-time analysis composes the response time of a real-time task.

> 表示实时任务行为的一种常见方法是使用图形格式。图[1](#\_ bookmark1)显示了响应时间分析中使用的每个抽象如何构成实时任务的响应时间。

# 3. A PARALLEL BETWEEN THE RESPONSE-TIME ANALYSIS AND LINUX

> ＃3.响应时间分析和 Linux 之间的平行

The kernel without the patch PREEMPT RT presents some execution contexts that make it hard to precisely define the abstraction of a task. But with PREEMPT RT, almost all of these contexts were transformed into kernel threads, including some parts of the interrupt handler’s work. On PREEMPT RT, many interrupt handlers are converted to run as kernel threads. For these interrupt handlers, their function is no longer to deal with the hardware but to wake up a kernel thread that will deal with the hardware. Nevertheless there are some exceptions to this rule, for example, to timer interrupt request (IRQ).

> 没有补丁的内核 RT 呈现出一些执行上下文，使得难以精确定义任务的抽象。但是有了抢先的 RT，几乎所有这些上下文都转变为内核线程，包括中断处理程序的某些部分。在抢占 RT 上，许多中断处理程序被转换为内核线程。对于这些中断处理程序，它们的功能不再处理硬件，而是要唤醒将处理硬件的内核线程。但是，该规则有一些例外，例如，计时器中断请求(IRQ)。

Regarding the user space, processes are composed by a memory context and a set of one or more threads. Nowadays, the Linux scheduler deals with threads, scheduling the system on a thread basis. Generally, a thread runs in the process memory context, but when a thread makes a system call or causes an interrupt, for example, with a page fault, it changes its execution context from user space to kernel space, executing the kernel code in kernel space on behalf of the process [15](#_bookmark46). Thus, it is possible to map the abstraction of a task into these two execution contexts that the Linux has: the interrupt handlers, which run only in kernel space, and the threads, which can run both in kernel and user spaces.

> 关于用户空间，过程由内存上下文和一组或多个线程组成。如今，Linux 调度程序处理线程，以线程为基础安排系统。通常，线程在过程内存上下文中运行，但是当线程进行系统调用或引起中断时，例如，使用页面故障时，它将其执行上下文从用户空间更改为内核空间，然后在内核中执行内核代码代表该过程[15](#\_ bookmark46)空间。因此，可以将任务的抽象映射到 Linux 具有的这两个执行上下文中：仅在内核空间中运行的中断处理程序以及可以在内核和用户空间中运行的线程。

Each activation of a task is known as a job. For the interrupt handlers, we assume that each interrupt is a new activation, so it is a job. Nevertheless, it is not easy to map the abstraction of job to threads.

> 任务的每个激活都称为工作。对于中断处理程序，我们假设每个中断都是新的激活，因此这是一项工作。然而，将作业的抽象映射到线程并不容易。

In the theory, a job executes without suspending itself. Thus, each time a job starts to run, it starts a new activation. And each time a job suspends, it finishes an activation. Coincidentally, Linux imposes the same restriction to the interrupt handlers, because an interrupt handler cannot suspend while running. So, each interrupt handler activation is a new job. However, this restriction does not exist for the tasks in the context of threads, as threads can suspend whenever it is running with interrupts and preemption enabled [15](#_bookmark46). A thread always suspends its execution running in kernel context. It does it by changing its state and calling the scheduler. Considering the operation without errors and debugging mechanisms, one thread may suspend for two reasons: by performing a blocking system call, usually leaving the CPU in _S_ state, or blocking in a mutual exclusion method, usually leaving the CPU in _D_ state. This paper considers that real-time threads may suspend at any time by locking mechanisms for mutual exclusion. However, it is assumed that a real-time thread does not suspend for another reason during execution, except to complete the activation. Thus, an unintentional suspension of a task in a locking mechanism is accepted. However, we consider that a job finishes its activation when it suspends outside of a lock mechanism.

> 从理论上讲，工作执行而不会暂停自己。因此，每次作业开始运行时，都会开始新的激活。每次工作暂停，都可以完成激活。巧合的是，Linux 对中断处理程序施加了相同的限制，因为中断处理程序在运行时无法暂停。因此，每个中断处理程序激活都是一项新工作。但是，在线程上下文中，任务不存在此限制，因为线程可以在启用中断并启用前抢先运行时暂停[15](#* bookmark46)。线程总是暂停其在内核上下文中运行的执行。它通过更改状态并调用调度程序来做到这一点。考虑到没有错误和调试机制的操作，一个线程可能有两个原因：通过执行阻止系统调用，通常将 CPU 留在\_s *状态下，或以相互排除方法阻止，通常将 CPU 留在* d*状态下。本文认为，实时线程可能随时通过锁定相互排除的机制暂停。但是，假定一个实时线程在执行过程中没有其他原因暂停，除了完成激活。因此，接受了锁定机制中任务的无意暂停。但是，我们认为，当工作悬挂在锁定机制之外时，工作就完成了激活。

## 3.1. Sources of release jitter

> ## 3.1。发行抖动的来源

The maximum release jitter, represented by variable _J_ , occurs when a higher-priority task is delayed at the beginning of its execution, being the delay caused by a lower-priority task. This may occur for both kinds of Linux tasks: interrupt handlers and threads.

> 由变量 _J_ 表示的最大发行抖动是在执行开始时延迟较高优先级任务的情况，这是由较低优先级任务造成的延迟。这两种 Linux 任务可能会发生这种情况：中断处理程序和线程。

### 3.1.1 _Interrupt handlers._

> ### 3.1.1 _ Interrupt Handlers._

The activation of interrupt handlers happens with the occurrence of interrupts. There is only one way a hardware interrupt is signaled, and it does not immediately stop the execution of a task: the system disabled that interrupt. An example of this delay is when processor interrupts are disabled, and soon after, there is the occurrence of a hardware interrupt. Because interrupts are disabled, the interrupt handling will be delayed until interrupts are enabled again, and its interrupt handler can finally execute.

> 中断处理程序的激活随着中断的发生而发生。只有一种方式发出了硬件中断的方式，并且不会立即停止执行任务：禁用该中断的系统。此延迟的一个例子是，当处理器中断被禁用时，不久之后，就会发生硬件中断。由于中断是禁用的，因此中断处理将被延迟，直到再次启用中断为止，其中断处理程序最终可以执行。

The possibility of disabling interrupts is required mainly to ensure synchronization. Disabled interrupts ensure that an interrupt handler will not cause preemption of a section of code.

> 主要需要禁用中断的可能性以确保同步。残疾人中断可确保中断处理程序不会导致一部分代码的抢占。

The Linux kernel includes functions to disable all maskable interrupts of a processor or to disable an interrupt on all processors. There are two ways to disable interrupts in the current processor: unconditionally or conditionally. The first is through the functions _local_irq_disable()_ and _local_irq_enable()_. The second is through the functions _local_irq_save()_ and _local_irq_restore()_; these functions (actually macros) save the processor flags only to be restored lately, which allow nesting calls to disable/enable interrupts [16](#_bookmark47).

> Linux 内核包含可禁用处理器的所有可掩蔽中断或禁用所有处理器中断的功能。有两种方法可以在当前处理器中禁用中断：无条件或条件地。第一个是通过函数 *local_irq_disable()*和* local_irq_enable()* *。第二个是通过函数\_local_irq_save()*和* local_irq_restore()*;这些功能(实际上是宏)保存了处理器标志，仅恢复了，允许嵌套调用禁用/启用中断[16](#\_ bookmark47)。

Besides being possible to disable all interrupts of a processor, in some cases, it is desirable to disable a specific interrupt on all processors. For example, you may need to disable the delivery of an interrupt before handling its state. The Linux kernel provides four functions for this task. The first function is _disable_irq(irq)_, which disables the interrupt passed as argument on all processors. If the interrupt handler is running, the function will block until the handler terminates. The function _disable_irq_nosync(irq)_ also disables the interrupt on all processors, however, without waiting for the interrupt handler that may be running [15](#_bookmark46). The function _synchronize_irq(irq)_ will wait for the interrupt handler of a specific IRQ before returning. Finally, the function _enable_irq(irq)_ enables the interrupt [16](#_bookmark47).

> 除了可以禁用处理器的所有中断之外，在某些情况下还希望禁用所有处理器上的特定中断。例如，您可能需要在处理状态之前禁用中断的交付。Linux 内核为此任务提供了四个功能。第一个函数是 _disable_irq(irq)_，它禁用所有处理器上的参数传递的中断。如果中断处理程序正在运行，则该功能将阻止直到处理程序终止。函数*disable_irq_nosync(IRQ)*还禁用所有处理器上的中断，但是，无需等待可能正在运行的中断处理程序[15](#* bookmark46)。函数\_synchronize_irq(IRQ)*将在返回之前等待特定 IRQ 的中断处理程序。最后，函数* enable_irq(irq)*启用中断[16](#\_ bookmark47)。

### 3.1.2 _Preemption._

> ###三。1*primpation.*

There is another source of release jitter when considering threads. Threads are activated by events that change their state in the scheduler, from sleeping to ready to execute. When a higher-priority thread is awakened by a lower-priority thread, the scheduler is called and starts execution of the thread of higher priority, unless preemption is disabled.[$‡$](#_bookmark5) When preemption is disabled, the lower-priority thread runs until preemption is enabled again and the scheduler can decide to run the thread of higher priority. The preemption of a processor can be disabled with the function _preempt_disable()_ and then enabled again with the function _preempt_enable()_. For each _preempt_disable()_, there should be a call to _preempt_enable()_. These calls can be nested; the number of nesting can be retrieved with the function _preempt_count()_ [15](#_bookmark46).

> 考虑线程时，还有另一个释放抖动的来源。线程会被调度程序中改变状态的事件激活，从睡觉到准备执行。当较低优先级线程唤醒更高优先级的线程时，调用调度程序被调用并开始执行较高的优先级线程，除非禁用了优先级。 - 优先线程一直运行，直到再次启用抢占，并且调度程序可以决定运行更高优先级的线程。可以使用函数 _preempt_disable()_ \_ _ PREENGOR 的优先考虑，然后再次使用函数\_preempt_enable()_ _。对于每个\_preempt_disable()_，应该打电话给 _preempt_enable()_。这些呼叫可以嵌套；可以使用函数 _preement_count()_ [15](#\_ bookmark46)检索嵌套的数量。

The function _preempt_enable()_, when called, checks whether the preemption counter will be 0, that is, whether the preemption system will be active again. Because it is possible that a higherpriority task is ready to run, when enabling preemption, the scheduling routine is called. In cases where one does not want to check for threads that are able to run, it is possible to use the function _preempt_enable_no_resched()_, which enables preemption again without checking if a new higherpriority task is able to run.

> 函数 _preempt_enable()_，当调用时，检查抢先计数器是否为 0，即，抢先系统是否会再次处于活动状态。因为有可能准备运行较高的优先级任务，因此在启用抢占时，调用计划例程。如果一个人不想检查能够运行的线程，则可以使用函数 _preempt_enable_no_resched()_，它可以再次进行抢先，而无需检查新的高级任务是否能够运行。

## 3.2 _Sources of blocking_

> ## 3.2 _阻止_

Blocking happens when a lower-priority task retains a lock requested by a higher-priority task. The Linux kernel has several mechanisms for mutual exclusion. There are two reasons for these several different mechanisms. The first comes from the fact that the Linux kernel presents two execution contexts: interruptions and threads, which have different constraints. In the context of interrupt handlers, the code cannot use methods that put the interrupt handler to sleep, because interrupts do not have a context that the scheduler can control, therefore mutual exclusion mechanisms must use busy waiting in case of contention. In the context of threads, the threads can sleep, allowing other threads to execute, while the blocked task waits for the resource.

> 当较低优先级任务保留较高优先级任务要求的锁定时，就会发生阻塞。Linux 内核具有多种相互排斥的机制。这些不同的机制有两个原因。第一个来自 Linux 内核呈现两个执行上下文的事实：中断和线程，它们具有不同的约束。在中断处理程序的上下文中，代码不能使用使中断处理程序入睡的方法，因为中断没有调度程序可以控制的上下文，因此相互排除机制必须使用忙碌的等待在争论中。在线程的上下文中，线程可以睡觉，允许其他线程执行，而被阻止的任务等待资源。

In addition to the restrictions imposed by the execution contexts of the Linux kernel, the methods of mutual exclusion are optimized for certain cases, some with the purpose of improving performance, others seeking determinism. Several methods of generating mutual exclusion that causes blocking in the Linux kernel are described in the following. As some of these methods are exclusive to the PREEMPT RT patch, each method is described whether it is part of the Linux kernel without PREEMPT RT, which is commonly called vanilla kernel, or it is part of the kernel PREEMPT RT.

> 除了 Linux 内核的执行环境所施加的限制外，相互排斥的方法还针对某些情况进行了优化，有些是旨在提高绩效的目的，而另一些则寻求确定性。下面描述了几种引起 Linux 内核中阻塞的相互排斥的方法。由于这些方法中的某些方法是抢占式 RT 补丁的独有，因此每种方法是否是 Linux 内核的一部分，而无需抢先 RT，通常称为 Vanilla 内核，还是它是内核 prement RT 的一部分。

### 3.2.1 _Spinlock._

> ### 3.2.1 _spinlock._

In a section protected by a spinlock, only one task is allowed access to a specific critical region. If a task tries to acquire a spinlock that is not held by any other task, the lock is acquired. If a task attempts to acquire a spinlock that has already been acquired by another task, the task is blocked. In the vanilla kernel, a task blocked on a spinlock is held at busy waiting while trying to acquire the spinlock, thus consuming CPU until another task releases the spinlock. An important detail is that before attempting to acquire a spinlock, the current task disables the preemption of the processor, enabling it again only after releasing the lock. When a task attempts to acquire a spinlock and stays in busy waiting, the task is said to be in contention [16](#_bookmark47).

> 在由 Spinlock 保护的部分中，只有一个任务可以访问特定的关键区域。如果一个任务试图获取任何其他任务没有持有的旋转锁，则将获取锁。如果一个任务试图获取另一个任务已经获取的单锁，则该任务被阻止。在香草内核中，在试图获取 Spinlock 的同时忙于等待，在忙碌的情况下，一项任务被阻止了，从而消耗了 CPU，直到另一个任务释放出 Spinlock 为止。一个重要的细节是，在尝试获取 Spinlock 之前，当前任务会禁用处理器的先发制位，仅在发布锁后才能再次实现。当任务尝试获取单锁并留在忙碌等待中时，该任务被认为是争夺的[16](#\_ bookmark47)。

Despite the fact that busy waiting for the lock consumes CPU time in vain, this avoids a more complex control to change the status of the task from ready to sleeping, to call the scheduler routines, to context switch to another task, and when the lock is available, to change the context to the task that awaits the lock. Thus, the busy-waiting kernel spinlock is beneficial when you have small critical sections [16](#_bookmark47). Several references such as [16](#_bookmark47) and [15](#_bookmark46) classify critical sections as small or large. However, there is not a threshold that defines the size of a small or large critical section, leaving it to the developer to judge the characteristic of the critical section. The spinlock is used especially in parts of the kernel where a task cannot sleep, as in interrupt handlers.

> 尽管忙于等待锁会徒劳地消耗 CPU 时间，但这避免了更复杂的控制，以将任务的状态从准备就绪，调用调度程序例程，到上下文切换到另一个任务，以及锁定可用，将上下文更改为等待锁的任务。因此，当您有少量关键部分时，忙碌的核心自旋锁[16](#_ bookmark47)是有益的。几个参考文献，例如[16](#_ bookmark47)和[15](#\_ bookmark46)将关键部分分类为小或大。但是，没有一个阈值定义一个小或大关键部分的大小，而将其留给开发人员来判断关键部分的特征。自旋锁尤其是在任务无法入睡的一部分中使用的，就像中断处理程序一样。

In the kernel with PREEMPT RT, spinlocks are converted to RT Mutexes. The reason for this change is described in Section [3.2.5](#_bookmark8).

> 在具有抢先 RT 的内核中，Spinlocks 转换为 RT 静音。此更改的原因在第[3.2.5](#\_ Bookmark8)中描述。

In order to use a spinlock to protect a critical section, it is necessary to acquire the spinlock, execute the critical section, and release the spinlock. For this, it uses the functions _spin_lock()_ and _spin_unlock()_. Also, by disabling the preemption during a critical section, the spinlocks affect the release jitter.

> 为了使用 Spinlock 保护关键部分，有必要获取自旋锁，执行临界部分并释放 Spinlock。为此，它使用函数 *spin_lock()*和* spin_unlock()*。同样，通过在关键部分中禁用预先抢先，Spinlock 会影响释放抖动。

In addition to the standard functions, the API of the spinlocks also implements versions that disable interrupts and the processing of softirqs; these functions are necessary to prevent deadlocks. An example for this is the following: a spinlock was acquired by a thread, then the execution of

> 除了标准函数外，Spinlock 的 API 还实现了禁用中断和软件处理的版本。这些功能是防止僵局的必要条件。一个例子是：

the critical section is interrupted by an interrupt, which tries to acquire the same spinlock, that will never be released because the previous thread is blocked by the interrupt handler. Thus, by turning off interrupts, spinlocks may also contribute to the release jitter of interrupt handlers.

> 临界部分被一个中断打断，该中断试图获取相同的自旋锁，这将永远不会释放，因为上一个线程被中断处理程序阻止。因此，通过关闭中断，Spinlocks 也可能有助于中断处理程序的释放抖动。

### 3.2.2 _Read–write spinlocks._

> ### 3.2.2 \_read -write spinlocks。

In some cases, critical sections are accessed multiple times for data reads and sometimes for the update. To improve the throughput of the system, exclusive access to these data is needed only when writing the data. There may be concurrent accesses to read the data. In this case, there is contention only when a task waits to write or tasks wait for a data being written [16](#_bookmark47). To acquire the rw*lock for reading, one uses functions \_read_lock()* and _read_unlock()_. For writing, one uses functions _write_lock()_ and _write_unlock()_. The kernel vanilla uses spinlocks to protect the write access. Thus, the read–write spinlocks disable preemption, contributing, while on a writing section, to the release jitter of higher-priority threads. In the kernel with PREEMPT RT, control access to critical sections is made with the RT Mutex. The read–write spinlocks also have versions that disable interrupts and softirqs. It is not possible to upgrade the _read_lock()_ to a _write_lock()_, as this causes a deadlock.

> 在某些情况下，要多次访问关键部分以进行数据读取，有时甚至是更新。为了改善系统的吞吐量，仅在编写数据时才需要对这些数据的独家访问。可能有同时访问读取数据。在这种情况下，仅当任务等待写作或等待编写数据时才存在争议[16](#_ bookmark47)。为了获取 RW *锁定的读数，人们使用功能\ \_read_lock()*和\_read_unlock()_。对于写作，一个人使用函数* write_lock()* and _write_unlock()_。内核香草使用 Spinlock 来保护写入访问。因此，读写自旋锁可禁用预先抢先，在写作部分中贡献了更高优先级线的释放抖动。在具有抢先 RT 的内核中，使用 RT MUTEX 进行控制访问关键部分。读写单锁还具有可禁用中断和 softirqs 的版本。由于这会导致僵局，因此无法将 *read_lock()*升级为* write_lock()* \_ _write_lock()_。

An important detail is that the readers always take precedence over the writers. While there is a reader in the critical section, the writer cannot run. Because readers can obtain the lock concurrently, even if a writer is waiting for the lock, new readers may acquire the lock and thus postpone indefinitely the acquiring of the lock by the writer.

> 一个重要的细节是读者总是优先于作家。虽然关键部分中有读者，但作者无法运行。因为读者可以同时获得锁，即使作者正在等待锁，新读者也可以获取锁，因此无限期地推迟作者获取锁。

### 3.2.3 _Semaphores._

> ### 3.2.3 _semaphores._

Unlike spinlocks, semaphores do not use busy waiting. When a task tries to acquire a semaphore and this is unavailable, the semaphore puts the task on a waiting list and changes the state of the task to sleeping, and the task leaves the processor. When the semaphore becomes available, one of the tasks in the queue is awakened, and it acquires the semaphore, continuing its execution. As the kernel has some restrictions on where a piece of code can sleep, semaphores cannot be used in the context of interrupts [15](#_bookmark46). Semaphores accept various tasks in their critical section. This is controlled by a counter, which is set at its creation. Although it is possible to implement mutual exclusion using a semaphore with counter set to one, this is not the best practice, being the Mutex as the correct choice. Mutexes are presented in Section [3.2.4](#_bookmark7). Two basic functions can be used to acquire a semaphore: _down()_ and _down_interruptible()_. The difference between the two modes is the way that the task is put to sleep: state interruptible or uninterruptible.

> 与 Spinlock 不同，信号量不会使用忙碌等待。当任务试图获取信号量并且不可用时，信号量将任务放在等待列表上，并将任务状态更改为睡觉，并且任务将处理器留下。当信号量可用时，队列中的一项任务被唤醒，并获取了信号量，继续执行。由于内核对一块代码可以在哪里睡觉有一些限制，因此在中断的情况下不能使用信号量[15](#_ bookmark46)。信号量在其关键部分中接受各种任务。这是由计数器控制的，该计数器是在创建时设置的。尽管可以使用 Counter 设置的信号量实现相互排除，但这不是最佳实践，而是 MUTEX 作为正确的选择。静音词在第[3.2.4]节中介绍(#_ bookmark7)。可以使用两个基本功能来获取信号：_Down()_ and _down_interruptible()_。两种模式之间的区别在于任务的睡眠方式：状态可中断或不间断。

If a signal is sent to a task in interruptible state, the task is awakened immediately and the signal delivered to the task. On the other hand, a task in state uninterruptible is not waked up, thus delivering of the signal is delayed until the task is awake and acquires the semaphore. Of these two, it is more common to use the so-called _down_interruptible()_. Function _up()_ releases the semaphore.

> 如果将信号发送到可中断状态的任务，则立即将任务唤醒，并将信号传递给任务。另一方面，状态不间断的任务不会唤醒，因此信号的传递延迟了，直到任务醒来并获取信号量为止。在这两个中，使用所谓的*Down_Interruptible()*更常见。函数* up()*释放信号量。

When compared with spinlocks, semaphores have an advantage: semaphores do not disable preemption throughout critical section, which helps in decreasing the release jitter.

> 与 Spinlock 相比，信号量具有优势：信号量不会在整个临界部分中禁用抢占，这有助于减少释放抖动。

However, semaphores cause greater overhead because they put the task to sleep and then wake it up after sometime. In cases of small critical sections, this overhead can be greater than the critical section itself, so it is advised only for large critical sections.

> 但是，信号量会导致更大的开销，因为它们使任务入睡，然后在一段时间后醒来。在较小的关键部分的情况下，该开销可能大于关键部分本身，因此仅建议大型关键部分。

Another side effect is that by making the task to sleep, it is possible for a high-priority task to suffer unlimited priority inversion. This is the case when a high-priority task is blocked by a low-priority task, which in turn cannot run because a medium-priority task holds the processor.

> 另一个副作用是，通过使任务入睡，高优先级任务可能会遭受无限的优先倒置。当高优先级任务阻止高优先级任务时，这种情况又无法运行，因为中等优先级的任务会保留处理器。

_Read–write semaphores._ As with spinlocks, semaphores also have a version for read–write. Read– write semaphores do not have counters; the rule is the same as read–write spinlocks: a writer requires mutual exclusion, but several concurrent readers are possible. The precedence of the readers over the writers is the same as with the read–write spinlocks, so it is possible for the writers to be blocked indefinitely.

> *read – write Semaphores.*与 Spinlocks 一样，信号量也有一个用于读取的版本。读取 - 写信号没有计数器；该规则与读取 - 写锁相同：作者需要相互排除，但是几个并发的读者是可能的。读者比作家的优先级与读写自旋锁相同，因此作者可以无限期地阻止作家。

The function to acquire the semaphore for reading is _down_read()_. For writing, it used the function _down_write()_. With read–write semaphores, it is possible to downgrade the state writer to the state reader. This is carried out with the function _downgrade_write()_.

> 获取读取信号的功能是 _down_read()_。对于写作，它使用了函数 _Down_write()_。使用 Read -Write Semaphores，可以将国家作家降级到国家读者。这是使用函数*Downgrade_write()*进行的。

### 3.2.4 _Mutex._

> ### 3.2.4 _mutex._

The mutex option was implemented as simple mutual exclusion to put tasks on contention to sleep, mainly to replace semaphores initialized with a count of 1. Despite having a behavior similar to a semaphore with a count of 1, the mutex has a simpler interface, better performance, and more use restrictions, which facilitates system debugging [16](#_bookmark47). To acquire a mutex, it used the function _mutex_lock()_. If the mutex is not available, the task is put to sleep. To release a mutex, the function used is _mutex_unlock()_. In comparison with spinlocks, mutexes have the same benefits and problems of counting semaphores initialized to one.

> MUTEX 选项被用作简单的相互排斥，以将任务放在参与性的睡眠中，主要是用 1 次数量的信号量替换 1.尽管具有类似于信号量的行为，但 MUTEX 具有更简单的界面，更好的界面，更好性能和更多使用限制，可促进系统调试[16](#_ bookmark47)。要获取 Mutex，它使用了函数\_mutex_lock()_。如果静音不可用，则将任务入睡。要释放 Mutex，使用的功能是 _mutex_unlock()_。与 Spinlock 相比，静音具有相同的好处和计数定位信号量的问题。

### 3.2.5 _RT mutex._

> ### 3.2.5 _rt Mutex._

The RT mutexes extend the semantics of mutexes with the priority inheritance protocol. In an RT mutex, when a low-priority task holds an RT mutex and this RT mutex is blocking a task of higher priority, the low-priority task inherits the higher-priority task. If the task that inherited the priority blocks on another RT Mutex, this propagates the priority to another task until the task that holds the RT Mutex releases the mutex that blocked the highest-priority task. This approach helps to reduce the blocking time of high-priority tasks, avoiding unbounded priority inversion [17](#_bookmark48).

> RT 静音词通过优先继承协议扩展了静音的语义。在 RT Mutex 中，当低优先级任务保留 RT MUTEX 时，此 RT Mutex 阻止了更高优先级的任务时，低优先级任务继承了更高优先级的任务。如果继承了另一个 RT Mutex 上的优先级块的任务，这将传播到另一个任务的优先级，直到保存 RT Mutex 的任务会释放阻止最高优先级任务的静音。这种方法有助于减少高优先级任务的阻塞时间，避免无限的优先倒置[17](#\_ bookmark48)。

_RT mutex and PREEMPT RT._ In the Linux kernel with the patch PREEMPT RT, spinlocks and mutexes are converted to RT mutexes. Spinlocks are converted to RT spinlocks, using the RT Mutex to implement mutual exclusion. This is possible because in the PREEMPT RT, many sections of the kernel, which were originally in interrupt context, were converted to threads running in the address space of the kernel, so the spinlocks used in these sections can be converted to RT Mutex. In parts of the kernel that cannot sleep even with the PREEMPT RT, the original spinlocks are used, with the prefix `raw_`, for example, `raw_spin_lock()`.

> *rt Mutex 和 prement Rt.*在 Linux 内核中，带有贴片的 RT，Spinlocks 和 Mutexes 被转换为 RT 静音。使用 RT Mutex 将 Spinlocks 转换为 RT Spinlocks，以实现相互排除。这是可能的，因为在抢占 RT 中，最初在中断上下文中的内核的许多部分被转换为在内核地址空间中运行的线程，因此这些部分中使用的 Spinlock 可以转换为 RT MUTEX。在内核的一部分，即使使用先发制人的 RT 也无法入睡，使用前缀 `raw_'使用了原始的Spinlock，例如raw_spin_lock()`。

A major benefit of transforming spinlocks in RT Mutexes comes from the fact that the RT Mutexes do not disable preemption. With this, the release jitter of threads tends to be smaller. In fact, the use of RT Mutexes instead of spinlocks and the execution of device interrupt handlers and softirqs in the context of threads are the two major causes for the decrease of latency in PREEMPT RT, when compared with the vanilla kernel.

> 在 RT 静音中转换 Spinlocks 的主要好处来自 RT 静音者不会禁用先发制人的事实。因此，线程的释放抖动往往较小。实际上，与 Vanilla 内核相比，在线程中使用 RT Mutexes 代替了 Spinlock，在线程中使用 RT 静脉锁以及在螺纹上下文中的执行设备中断处理程序和 SoftIRQ 是 prement RT 延迟的两个主要原因。

### 3.2.6 _Read–copy–update._

> ### 3.2.6 _read -copy – update._

The read–copy–update (RCU) is a synchronization mechanism. However, because it uses some features of the architectures of current processors such as the atomicity of operations with pointers aligned in memory, the RCU allows a writer and multiple readers in a critical section, concurrently. It thus achieves better performance when compared with the read–write spinlocks [18](#_bookmark49), [19](#_bookmark50). Figure [2](#_bookmark9) makes a comparison between the read–write spinlocks and the RCU.

> 读取 - 复制 - 统一(RCU)是一种同步机制。但是，由于它使用了当前处理器的架构的某些功能，例如在内存中对齐的操作的原子性，因此 RCU 同时允许作者和多个读者同时在关键部分中。因此，与读取– Write Spinlocks [18](#_ bookmark49)，[19](#_ bookmark50)相比，它可以实现更好的性能。图[2](#\_ bookmark9)进行了读取式旋转锁与 RCU 之间的比较。

![](./media/image10.png)

<Figure 2. Comparison between read–write (rw) spinlock and read–copy–update (RCU) [20](#_bookmark51). >

When updating an existing data, the task of the writers is divided into two parts. First, it updates the data, and this is carried out without blocking. If it wants to free the old data, the updater needs to wait until all the readers who have access to the old version of the data complete their read-side critical section, to then be able to free the old data.

> 更新现有数据时，作者的任务分为两个部分。首先，它更新数据，并在没有阻塞的情况下进行。如果要释放旧数据，更新程序需要等到所有能够访问数据旧版本的读者完成其读取端临界部分，然后才能释放旧数据。

Readers never block. The RCU ensures that accessed data will always be consistent. However, the data may or may not be current. The RCU API has several calls. However, its use can be illustrated with some basic functions.

> 读者永远不会阻止。RCU 确保访问的数据将始终保持一致。但是，数据可能是也可能不是当前的。RCU API 有几个电话。但是，可以用一些基本功能来说明其使用。

Functions _rcu_read_lock()_ and _rcu_read_unlock()_ are used by readers, to signal the entry and exit of the critical section for reading. A thread is not allowed to sleep between these two calls. These operations can be nested.

> 读者使用函数 *rcu_read_lock()*和* rcu_read_unlock()* \_使用，向关键部分的入口和出口发出信号。线程不允许在这两个呼叫之间睡觉。这些操作可以嵌套。

Function _synchronize_rcu()_ is used by the writer. This will mark the end of its operation by defining a partition between old readers, which may have access to the removed data, and new readers that cannot access the newly removed data. This function blocks the writer until all readers with the old reference have left the critical section. It is possible to implement this operation without blocking, by using function _call_rcu()_. This function registers a callback that will be called after all readers finished their critical sections. Besides the basic functions exemplified here, there are other functions that have the same role but with restrictions and different application areas. A table with the complete API is available in [21](#_bookmark52).

> 函数*synchronize_rcu()*由作者使用。这将通过定义旧读者之间的分区来标记其操作的终结，该读者可以访问删除的数据，以及无法访问新删除的数据的新读者。此功能会阻止作者，直到所有具有旧参考的读者都离开了关键部分。通过使用函数* call_rcu()*可以实现此操作而无需阻止。此函数会记录一个回调，所有读者都完成了关键部分。除了这里举例说明的基本功能外，还有其他功能具有相同的作用，但具有限制和不同的应用领域。具有完整 API 的表可在[21](#\_ bookmark52)中使用。

Compared with read–write spinlocks, RCU has the benefit of not indefinitely delaying the writers. Even in the presence of readers, RCU allows writers to update the data. RCU is being increasingly used in the Linux kernel.

> 与读取式旋转锁相比，RCU 的好处是不要无限期地延迟作家。即使在读者的存在下，RCU 也允许作家更新数据。RCU 越来越多地用于 Linux 内核中。

## 3.3 _Kernel mechanisms and the response-time analysis_

> ## 3.3 _KERNEL 机制和响应时间分析_

This section presents the mapping of the Linux kernel mechanisms, listed in Sections [3.1](#_bookmark4) and [3.2](#_bookmark6), to the abstractions used in the response-time analysis, described in Section [2](#_bookmark0). This mapping is described in Table [I](#_bookmark10). It can be seen that several synchronization mechanisms are used within the kernel; each of them may generate blocking. The release jitter happens because of the control mechanisms of interruption and preemption.

> 本节介绍了 Linux 内核机制的映射，该机制在第[3.1](#_ bookmark4)和[3.2](#_ bookmark6)中列出的响应时间分析中使用的抽象分析中使用，在[2](#_kbookmark0 中描述))。该映射在表[i](#_ bookmark10)中描述。可以看出，内核中使用了几种同步机制。它们每个都可能产生阻塞。释放抖动发生是由于中断和抢先的控制机制。

In addition to the points of interest mapped in this section, because of some restrictions of the response-time model, we added other points of interest that assist in understanding the constraints imposed by Linux.

> 除了本节中映射的兴趣点之外，由于响应时间模型的某些限制，我们还增加了其他兴趣点，以帮助理解 Linux 施加的约束。

### 3.3.1 _Task migration._

> ### 3.3.1 \_task 迁移。

The response-time method is valid only for mono-processed systems, which does not represent the majority of current real-time Linux research and usage. An important issue for multicore systems is how the system allocates the tasks on the CPUs.

> 响应时间方法仅适用于单个处理的系统，这并不代表当前的实时 Linux 研究和使用中的大多数。多功能系统的一个重要问题是该系统如何在 CPU 上分配任务。

Table I. Mapping between mechanisms of the Linux kernel and abstractions of the response-time analysis.

> 表 I. Linux 内核机理与响应时间分析的抽象之间的映射。

> ===

According to Davis and Burns [13], multicore systems can be classified into three categories:

> 根据戴维斯(Davis)和伯恩斯(Burns)[13]，多核心系统可以分为三类：

1. No migration: each task is allocated to a processor, and no migration is permitted.

> 1.不迁移：每个任务都分配给处理器，也不允许迁移。

2. Task-level migration: the jobs of a task may execute on different processors; however, each job can only execute on a single processor.

> 2.任务级迁移：任务的作业可以在不同的处理器上执行；但是，每个作业只能在单个处理器上执行。

3. Job-level migration: a single job can migrate to and execute on different processors; however, parallel execution of a job is not permitted.

> 3.工作级别的迁移：单个作业可以在不同的处理器上迁移并执行；但是，不允许并行执行工作。

Using the mapping between tasks and Linux execution mechanisms, it is possible to categorize Linux’s interrupt handlers and threads. According to [22](#_bookmark53), it is possible to classify the interrupts as global or local. Local interrupts are those that run on a fixed processor, and global are those that can run on any processor. Local interrupts can be classified as no migration, as they always run on the same processor. On the other hand, global interrupts can be classified as task-level migration, as they can be migrated from one processor to another. But once an interrupt started an activation, it cannot be migrated.

> 使用任务和 Linux 执行机制之间的映射，可以对 Linux 的中断处理程序和线程进行分类。根据[22](#\_ bookmark53)，可以将中断分类为全局或本地。本地中断是在固定处理器上运行的那些中断，而全局可以在任何处理器上运行。本地中断可以分类为无迁移，因为它们总是在同一处理器上运行。另一方面，可以将全局中断归类为任务级迁移，因为它们可以从一个处理器迁移到另一个处理器。但是，一旦中断开始激活，就无法迁移。

For threads, this classification depends on a set of system configurations. A thread may be configured to run on one of _m_ processors, where _m_ is the number of processing units, which may be a core or thread (regarding hyper-threading), here denoted only as processor. Considering the case in which a task is associated with only one processor, it can be classified as no migration. For other cases, where a task can migrate between two or more processors, it is possible to classify the task as job-level migration, because a task can migrate at any time during its activation, except when preemption or migration are disabled or when an interrupt is interfering with the execution of this thread.

> 对于线程，此分类取决于一组系统配置。可以将线程配置为在一个 _m_ 处理器之一上运行，其中 _m_ 是处理单元的数量，可能是核心或线程(关于超线程)，此处仅表示为处理器。考虑到任务仅与一个处理器关联的情况，可以将其归类为无迁移。对于其他情况，一个任务可以在两个或多个处理器之间迁移的情况中断正在干扰该线程的执行。

Regarding the processors, it is interesting to know in which CPU each task is running. For threads that can migrate, it is also interesting to know when these tasks were migrated and to which processor. To ensure the consistency of some operations, it is possible to temporarily disable the migration of threads on Linux. This is carried out using the _migrate_disable()_ and _migrate_enable()_ functions, in order to disable and enable the migration capability of a thread.

> 关于处理器，有趣的是，每个任务正在运行哪个 CPU。对于可以迁移的线程，知道这些任务何时迁移以及到哪个处理器也很有趣。为了确保某些操作的一致性，可以暂时禁用 Linux 上线程的迁移。这是使用*migrate_disable()*和* migrate_enable()*函数进行的，以便禁用并启用线程的迁移能力。

### 3.3.2 _Scheduling overhead._

> ### 3.3.2 \_scheduling 开销。

Another restriction of the response-time analysis model is the scheduling overhead. In most theoretical studies, the scheduling overhead is usually considered negligible, or it is assumed that the overhead can be added to the computation time of the tasks.

> 响应时间分析模型的另一个限制是调度开销。在大多数理论研究中，调度开销通常被认为可以忽略不计，或者假定可以将开销添加到任务的计算时间中。

Regarding empirical studies, it is quite common to observe measurements of scheduling overhead. It is usually measured the overhead associated with selecting the next task to be scheduled or the context switching overhead. These overheads are measured primarily to determine an upper bound or to compare different implementations of schedulers [7](#_bookmark38), [23](#_bookmark54).

> 关于实证研究，观察日程安排开销的测量很普遍。通常，它测量与选择要安排的下一个任务或上下文开销相关的开销。这些开销主要是为了确定上限或比较调度程序的不同实现[7](#_ bookmark38)，[23](#_ bookmark54)。

In Linux, both functions are performed inside the _schedule()_ function and other functions relevant to the scheduling of tasks. In order to demonstrate when the scheduler functions are called and how these functions influence the execution of threads, we added the tracing of the functions that perform the scheduling, including all the overhead involved in its implementation.

> 在 Linux 中，两个函数均在*schedule()*函数和与任务计划相关的其他功能中执行。为了证明调用调度程序函数何时调用以及这些函数如何影响线程的执行，我们添加了执行调度的功能的跟踪，包括其实现中涉及的所有开销。

# 4. TRACE TIMEFLOW: A NEW TRACE TOOL

> ＃4.跟踪时流：一种新的跟踪工具

Trace tools are frequently used in the analysis of real-time Linux implementations [24](#_bookmark55)–[27](#_bookmark57). The main motivations for the utilization of trace, rather than alternatives such as logging and debugging, come from the fact that trace tools have as an objective low overhead and the ability of massively collecting and storing data during execution [26](#_bookmark56). Many trace tools have been developed and the most used are Feather-tracer, Ftrace and LTTng [27](#_bookmark57).

> 跟踪工具经常用于实时 Linux 实现的分析[24](#_ bookmark55) - [27](#_ bookmark57)。使用痕迹的主要动机，而不是诸如记录和调试之类的替代方案，这是一个事实，即跟踪工具具有客观的低开销以及在执行过程中大量收集和存储数据的能力[26](#_ bookmark56)。已经开发了许多跟踪工具，最常用的是羽毛跟踪器，ftrace 和 lttng [27](#_ bookmark57)。

Feather-trace is an event trace tool designed to be used with imus$RT$ [28](#_bookmark58). imus$RT$ is a project composed by a _patch_ to the Linux kernel, a set of libraries, and tools that provide support to the development of real-time multiprocessor schedulers on Linux [3](#_bookmark34). Feather-trace enables the trace of events, being used mainly in articles that describe imus$RT$ ’s implementations. For this reason, it covers only the points of interest of imus$RT$ , not covering all aspects of the Linux execution, such as locking mechanisms. Thus, it is not currently possible to trace all the Linux execution using only the Feather-tracer.

> Feather-trace 是一种事件跟踪工具，旨在与 IMUS $ RT $ [28](#* bookmark58)一起使用。IMUS $ RT $是一个由\_patch*组成的项目，向 Linux 内核(一组库)和工具，可为 Linux 上实时多处理器调度程序的开发提供支持[3](#\_ bookmark34)。Feather-trace 可以实现各种事件，主要用于描述 IMUS $ RT $实现的文章。因此，它仅涵盖 IMUS $ RT $的兴趣点，而不是涵盖 Linux 执行的所有方面，例如锁定机制。因此，目前不可能仅使用羽毛跟踪器跟踪所有 Linux 执行。

Ftrace is the standard trace tool for the Linux kernel. It enables the trace of events, with _tracepoints_ [29](#_bookmark59), and functions, with the _function tracer_ [30](#_bookmark60). Ftrace also implements trace plugins. These plugins are used to make measurements and analyses of the Linux kernel. For example, the `function_graph` plugin traces the function’s call and return and gives the execution time of each function. The `irqsoff` plugin measures the longest IRQ-disabled section, reporting the trace of the functions that were executed in this section.

> Ftrace 是 Linux 内核的标准跟踪工具。它可以使用 _tracepoints_ [29](#_ bookmark59)和功能，并使用\_function tracer_ [30](#\_ bookmark60)启用事件的痕迹。Ftrace 还实现了跟踪插件。这些插件用于对 Linux 内核进行测量和分析。例如，`function_graph` 插件跟踪函数的调用并返回，并给出每个函数的执行时间。“ IRQSOFF”插件测量了最长的 IRQ 删除部分，报告了本节中执行的功能的跟踪。

However, these tools are strongly related to the current form of real-time Linux analyses. It is necessary a new trace plugin in order to provide a new view over the Linux execution, based on the abstractions of the real-time scheduling theory.

> 但是，这些工具与当前的实时 Linux 分析形式密切相关。必须根据实时调度理论的抽象来提供有关 Linux 执行的新视图，以便提供一个新的跟踪插件。

The LTTng is another trace tool used in real-time experiments [31](#_bookmark61). With regard to the tracing of the Linux kernel, LTTng uses the same trace forms of Ftrace. The difference is in the way that LTTng manages the trace sections, making possible concurrent trace sections, in the interface that it uses to communicate with the user space, in the trace format, and in the tools available to analyze the trace output.

> LTTNG 是实时实验中使用的另一个跟踪工具[31](#\_ bookmark61)。关于 Linux 内核的追踪，LTTNG 使用了相同的痕迹形式的 ftrace。区别在于 LTTNG 管理跟踪部分，使可能并发的跟踪部分，在其用于与用户空间，跟踪格式以及可用于分析跟踪输出的工具中使用的接口。

As the LTTng and Ftrace share the same trace forms, this work will use the Ftrace as the initial interface, but it is also possible to integrate the new trace plugin with LTTng. In the next section, we first review Ftrace; we then present the new trace tool proposed in this paper, called Trace Timeflow.

> 由于 LTTNG 和 FTRACE 共享相同的跟踪表单，因此该工作将使用 Ftrace 作为初始接口，但是也可以将新的 Trace 插件与 LTTNG 集成。在下一节中，我们首先审查 Ftrace；然后，我们介绍本文提出的新的微量工具，称为 Trace TimeFlow。

## 4.1 _Introduction to Ftrace_

> ## 4.1 _ introduction for ftrace_

The Ftrace’s user interface was built on top of _debugfs_, which is a debug filesystem of the Linux kernel. With _debugfs_, the trace’s configuration and data collection can be carried out with the commands _echo_ and _cat_. This interface exempts the use of more complex tools [30](#_bookmark60) because all data processing and formatting are carried out in the kernel itself.

> Ftrace 的用户界面是在 _debugfs_ 顶部构建的，该 _debugfs_ 是 Linux 内核的调试文件系统。使用 _debugfs_，可以使用命令 _echo_ 和 _cat_ 进行跟踪的配置和数据收集。该接口免除了更复杂的工具的使用[30](#\_ bookmark60)，因为所有数据处理和格式均在内核本身中进行。

Ftrace supports these three kinds of trace:

> Ftrace 支持这三种痕迹：

- Static using _tracepoints_ [29](#_bookmark59);

> - 使用 _tracepoints_ [29](#\_ bookmark59)静态;

- Static on the call and return functions using _function_ and _function graph_ tracer [32](#_bookmark62);

> - 使用函数和功能图形示踪剂[32](#\_ bookmark62)静态呼叫和返回函数;

- Dynamic using _kprobe_ [33](#_bookmark63).

> - 使用 _kprobe_ [33](#\_ bookmark63)动态。

This article uses two of these three trace methods: the tracepoints and _function graph_ tracer.

> 本文使用了这三种跟踪方法中的两种：TracePoints 和 _Function Graph_ Tracer。

The tracepoints are points of trace that can be added at any place of the kernel. It was created to replace the various existing forms of debug of Linux. The main characteristics of tracepoints are as follows:

> 跟踪点是可以在内核的任何位置添加的迹线点。它的创建是为了替换 Linux 的各种现有形式的调试形式。痕迹的主要特征如下：

- Can be used at any point in the kernel;

> - 可以在内核中的任何时刻使用；

- Low overhead in the decision to run or not run the trace, especially in the second case;

> - 在决定运行或不运行轨迹的决定中，尤其是在第二种情况下；

- Efficient storage of data;

> - 有效存储数据；

- Conversion of raw data into intuitive information.

> - 将原始数据转换为直观信息。

A set of macros was developed to facilitate the use and adoption of tracepoints. These macros emulate automatic code generation, automating the process of creating new trace points.

> 开发了一组宏来促进痕量的使用和采用。这些宏模仿自动代码生成，使创建新的跟踪点的过程自动化。

The other form of trace is the function tracer. The function tracer relies on the way the GNU C Compiler (GCC) and the Gprof profiling tool interact with applications in user space. When an application is compiled with option -pg of GCC, a call to the function _mcount_ is added in the beginning of each function. After a function is executed, it calls the function _mcount()_.

> 迹线的另一种形式是函数示踪剂。该功能示踪剂依赖于 GNU C 编译器(GCC)和 GPROF 分析工具与用户空间中的应用程序进行交互的方式。当使用 GCC 的选项-PG 编译应用程序时，在每个函数的开头中添加了对函数 _mcount_ 的调用。执行函数后，它调用函数 _mcount()_。

The function _mcount()_ receives two arguments: the address of the function that called _mcount()_ and the return address of the function that called _mcount()_. For example, the function _foo()_ called the function _bar()_, which called _mcount()_. The first argument of _mcount()_ is the address of the function _bar()_, and the second argument is the return address of function _bar()_, which is in the function _foo()_.

> 函数 *mcount()*接收两个参数：称为* mcount()*的函数的地址以及称为* mcount()*的函数的返回地址。例如，函数* foo()*调用函数* bar()*，该函数称为 _mcount()_。*mcount()*的第一个参数是函数* bar()*的地址，第二个参数是函数* bar()*的返回地址，该地址在 function _foo()_ \_。

Using this technique, Ftrace changes the _mcount()_ function to its own trace function, which aims at saving the addresses of functions in its buffer, along with other system information such as the status of interrupts and preemption. When Ftrace reads its buffer, it translates the address of the functions to the name of functions, thus showing the trace of all functions the kernel executed. In a simple example, the function tracer displays the following output:

> 使用此技术，FTRACE 将*mcount()*函数更改为其自己的跟踪功能，该功能旨在保存其缓冲区中功能的地址以及其他系统信息，例如中断和先发制位的状态。当 Ftrace 读取其缓冲区时，它将功能的地址转换为函数名称，从而显示了内核执行的所有函数的跟踪。在一个简单的示例中，函数示踪剂显示以下输出：

![](./media/image14.png)

In addition to the function trace, there are other trace plugins, with emphasis on the function graph. The function graph traces the call and return of a function. To improve the understanding of the stack of functions, the output shows the indentation of the functions according to its position in the stack.

> 除了函数跟踪外，还有其他轨迹插件，重点是函数图。功能图跟踪函数的调用和返回。为了提高对函数堆栈的理解，输出根据函数在堆栈中的位置表示缩进。

This is an example of the execution of the function graph:

> 这是函数图的执行的一个示例：

![](./media/image18.png)

An advantage of the function graph is the ability to determine the execution time of a particular function. It also makes the trace easy to follow, because of the indentation of functions. Ftrace allows the combined use of trace plugins and tracepoints.

> 功能图的优点是能够确定特定函数的执行时间。由于功能的凹痕，它也使痕迹易于遵循。FTRACE 允许联合使用跟踪插件和跟踪点。

The tracer proposed in this article, denominated Trace Timeflow, was created based on the function graph tracer, in order to trace the relevant functions. It also uses tracepoints to trace important changes in the system state.

> 本文中提出的示踪剂是基于函数图形示踪剂创建的，以指定的跟踪时间流，以追踪相关函数。它还使用跟踪点来追踪系统状态的重要变化。

## 4.2 _Trace timeflow_

> ## 4.2 _ Trace TimeFlow_

Initially, the new plugin was built as a copy of function graph. From this clone, changes were made to meet our needs. The first change was the fields to be displayed in the trace.

> 最初，新插件是作为功能图的副本构建的。从这个克隆中，进行了更改以满足我们的需求。第一个更改是要显示在跟踪中的字段。

### 4.2.1 _Trace format._

> ### 4.2.1 \_ trace 格式。

The format of the trace consists of six fields, as in the following example:

> 痕迹的格式由六个字段组成，如以下示例：

![](./media/image21.png)

The field _TASK-PID_ identifies the task running, it displays the name of the process and its PID.

> 字段 _task-pid_ 标识运行的任务，它显示过程的名称及其 pid。

The field _PRIO_ displays the priority. Currently, Linux has 140 priorities, where priority 0 is the highest and 139 is the lowest. The real-time tasks use priorities from 0 to 99, with priorities from 100 to 139 used as time-sharing priorities.

> 字段 _prio_ 显示优先级。目前，Linux 具有 140 个优先级，其中优先级为最高，而 139 是最低的。实时任务使用优先级从 0 到 99，优先级从 100 到 139 用作时间分布的优先级。

The field _CPU_ displays the CPU where the task is running.

> 字段 _CPU_ 显示任务正在运行的 CPU。

The field _TIME_ displays the absolute instant of time in which the event occurred.

> 字段 _time_ 显示事件发生的绝对时间。

The field _DURATION_ displays two types of information. The first is the execution time of functions, which is displayed in the return of the function, in nanoseconds. Secondly, this field is used to notify the entry points in the kernel.

> 字段 _Duration_ 显示两种类型的信息。第一个是函数的执行时间，该函数的执行时间在函数返回中显示在纳米秒中。其次，该字段用于通知内核中的入口点。

The field _FUNCTION CALLS_ displays the functions performed and tracepoint information.

> 字段* function 呼叫*显示执行的函数和跟踪点信息。

### 4.2.2 _Filter of functions._

> ### 4.2.2 _ functions._ filter.\_

Currently, Ftrace enables the filter functions to be displayed. To do so, it uses a linear search in a vector where the addresses of the desired functions are registered. The problem of this method is its complexity _O(n)_. In order to reduce the overhead in the selection of functions that must be tracked, it was used a technique already used by Ftrace, not for selecting functions but to determine whether or not particular function is an interrupt handler. To identify an interrupt handler, these functions were grouped in a section of text of the kernel binary. Thus, knowing the address of the beginning and end of this section, it is possible to determine whether or not a function is an IRQ handler. By using this same technique, the method of selection of functions becomes _O(l)_. The same technique was used to group the functions that implement mutual exclusion, scheduling, and system calls.

> 当前，FTRACE 可以显示过滤器功能。为此，它在注册所需功能的地址的向量中使用线性搜索。该方法的问题是其复杂性 _o(n)_。为了减少必须跟踪的函数选择中的开销，它被使用了 Ftrace 已经使用的技术，而不是选择功能，而是确定特定函数是否是中断处理程序。为了识别中断处理程序，将这些功能分组为内核二进制文本的一部分。因此，知道本节开始和结束的地址，可以确定函数是否是 IRQ 处理程序。通过使用相同的技术，函数选择的方法变为 _o(l)_。使用相同的技术来对实现相互排除，调度和系统调用的功能进行分组。

### 4.2.3 _Kernel entry points._

> ### 4.2.3 \_kernel 入口点。

The activation of the kernel code can be carried out either by hardware or by a process in user space. The hardware asynchronously activate the hardware interrupt routines in the kernel. This activation is made through a device interrupt, non-maskable interrupt (NMI), _traps_, and so on. In the user context, processes can run kernel routines synchronously with system calls or asynchronously with interrupts, for example, in a _page fault_.

> 内核代码的激活可以通过硬件或用户空间中的过程进行。硬件异步会激活内核中的硬件中断例程。通过设备中断，不可掩盖的中断(NMI)，_traps_ 等进行激活。在用户上下文中，进程可以与系统调用同步运行内核例程，也可以与中断相异步运行，例如在 _page FARD_ 中。

In order to facilitate the identification of entry points, the entry and exit of IRQ handlers are, respectively, signaled by flags ==========>_ and <========= in the \_DURATION_ field. For the system calls, the flags ———–>\_ and <——– are displayed in the call and return of the function that implements them.

> 为了促进入口点的识别，IRQ 处理程序的入口和退出分别由 flags ================> * and <====================\_Duration*字段。对于系统调用，标志 - - - - > \ \_和 < - - 在实现它们的函数的呼叫和返回中显示。

### 4.2.4 _Preemption._

> ### ౪ ౪.

Because it is possible to nest the call of the functions that control the preemption, tracepoints were added in order to display only when there is a change in the state of preemption. These tracepoints receive as argument the address of the function that enabled or disabled preemption. In the following, it is shown an example of the output of these tracepoints.

> 因为可以嵌套控制抢占的功能的呼叫，所以添加跟踪点才能仅在预先抢占状态发生更改时显示。这些跟踪点作为参数接收到启用或禁用的抢占函数的地址。在下文中，显示了这些跟踪点的输出的示例。

<img src="./media/image23.png" style="width:4.91321in;height:0.16844in" />

### 4.2.5 _IRQ control._

> ### 4.2.5 _irq Control._

In a way that is similar to preemption control, it is possible to nest calls to disable and enable IRQs. However, what matters for the analysis is the time when there is a change in the state of interrupts, from enabled to disabled or disabled to enabled. Thus, we added two tracepoints, which display when there is a change in the state of interrupts. An example of using these tracepoints is displayed as follows:

> 在类似于抢先控制的方式中，可以嵌套呼叫以禁用和启用 IRQ。但是，对于分析而言，重要的是，从启用到禁用或启用的中断状态发生变化的时间。因此，我们添加了两个跟踪点，它们在中断状态发生变化时显示。使用这些跟踪点的一个示例如下显示：

<img src="./media/image24.png" style="width:4.84802in;height:0.17354in" />

We also added tracepoints that show when a particular interrupt is disabled and enabled on all CPUs. Because it is not possible to nest these calls, it was only necessary to add points of trace to the functions that enable and disable the interrupt.

> 我们还添加了痕迹，这些跟踪点显示了在所有 CPU 上禁用特定中断并启用特定中断时。因为不可能嵌套这些调用，所以只需要将跟踪点添加到启用和禁用中断的函数中。

### 4.2.6 _Blocking._

> ### 4.2.6 _ blocking._

For the functions that implement the blocking mechanisms listed in Section [3.2](#_bookmark6), it was used both the trace of functions and tracepoints. In order to identify which type of block that is being used, and their behavior, the functions that implement these methods are displayed in the trace. Furthermore, it was used the following _tracepoints_ to inform the acquisition, blocking, and release of lock variables:

> 对于实现第[3.2](#* bookmark6)中列出的阻止机制的功能，它既使用函数的跟踪和跟踪点。为了确定所使用的块类型及其行为，实现这些方法的函数在跟踪中显示。此外，它被使用以下\_tracepoints *通知锁定变量的采集，阻止和发布：

- lock_acquire: indicates that the task wants to acquire the lock;

> -lock_acquire：指示任务要获取锁；

- lock_acquired: indicates that the task acquired the lock;

> -lock_acquired：指示任务获取了锁；

- lock_contended: indicates that the task was blocked in a lock;

> -lock_contended：指示任务被锁定在锁中；

- lock_release: indicates that the task released the lock.

> -lock_release：指示任务释放了锁。

### 4.2.7 _Scheduling overhead._

> ### 4.2.7 \_scheduling 开销。

It was used the trace of functions and tracepoints for scheduling operations. The scheduling functions are displayed to show the time when the task stops running application code and starts to execute the code of the scheduler.

> 它被用于调度操作的函数和跟踪点的跟踪。显示调度函数以显示任务停止运行应用程序代码并开始执行调度程序的代码的时间。

To display the scheduling decisions of the system, it was used the following existing tracepoints:

> 为了显示系统的调度决策，使用以下现有跟踪点：

- sched_wakeup: notifies when a task changes its state from sleeping to ready to run;

> -sched_wakeup：通知任务何时将其状态从睡眠变为准备就绪；

- sched_wakeup_new: notifies when a new task state changes its state from sleeping to ready to run;

> -sched_wakeup_new：通知新任务状态何时将其状态从睡眠变为准备就绪；

- sched_switch: notifies a context switch of tasks, also shows when a task has changed its state from ready to sleeping;

> -Sched_switch：通知任务的上下文开关，还显示了任务何时将其状态从准备就绪更改为睡眠；

- sched_migrate_task: notifies the migration of a task from one processor to another;

> -sched_migrate_task：通知任务从一个处理器到另一处理器的迁移；

- sched_pi_setprio: notifies a change in the priority of a process, caused by the priority inheritance protocol.

> -sched_pi_setprio：通知由优先级继承协议引起的流程优先级的更改。

### 4.2.8 _Task migration._

> ### 4.2.8 \_task 迁移。

Process migration is disabled and enabled by the functions _migrate_disable()_ and _migrate_enable()_. These calls can be nested. Thus, these tracepoints were added to show only when the system changes the migration state from enabled to disabled and vice versa. An example of the output of these tracepoints is the following:

> 过程迁移被函数 _migrate_disable()_ and _migrate_enable()_ \_ \_。这些呼叫可以嵌套。因此，仅当系统将迁移状态从启用到残疾人，反之亦然时，添加了这些跟踪点才显示。这些跟踪点的输出的一个示例是：

<img src="./media/image25.png" style="width:5.12534in;height:0.17in" />

# 5. CHARACTERIZATION OF THE LINUX PREEMPT RT TIMELINE

> ＃5. Linux 抢占 RT 时间轴的表征

This section describes the creation of an experimental environment to use the trace tool and the characterization of the execution of real-time tasks on Linux, using the abstractions of the real-time systems theory.

> 本节介绍了使用实时系统理论的抽象来创建实验环境来使用痕量工具以及在 Linux 上执行实时任务的表征。

A computer with an eight-core Intel Xeon E5260 processor and 4 GB of RAM was used for the experiments. On this system, the Fedora Linux distribution was installed, along with the 3.6 kernel, compiled with the PREEMPT RT patch and the new trace tool.

> 具有八核 Intel Xeon E5260 处理器和 4 GB RAM 的计算机用于实验。在此系统上，安装了 Fedora Linux 分布以及 3.6 内核，并与 Prement RT 补丁和新的 Trace Tool 一起编译。

In order to simulate the behavior of real-time tasks, two pieces of software were created. They are a periodic task that runs as a thread in user space and a module that runs in the Linux kernel. This task is identified as _pi_.

> 为了模拟实时任务的行为，创建了两个软件。它们是一项定期任务，可作为用户空间中的线程和在 Linux 内核中运行的模块运行。此任务被识别为 _pi_。

At each periodic activation, the user space thread activates the kernel module via a character device interface. The activation is carried out by reading or writing the module’s interface. When writing the module, the user space thread configures the duration of the busy wait that will be performed inside the kernel, during the _read()_ operations.

> 在每个周期性激活时，用户空间线程通过字符设备接口激活内核模块。激活是通过读取或编写模块的界面来进行的。编写模块时，用户空间线程在*read()*操作过程中配置将在内核内执行的繁忙等待的持续时间。

While reading the module, the task will try to acquire a lock, when there may be contention. After acquiring the lock, the task will perform a busy waiting, by the amount of time set through the _write()_ operation. After finishing the busy waiting, the lock is released and the thread execution returns to user space.

> 在阅读模块时，任务将在可能有争议的情况下尝试获取锁定。获得锁后，任务将通过*write()*操作设置的时间进行忙碌的等待。完成繁忙的等待后，锁定锁定，线程执行将返回用户空间。

This task executes without voluntary suspending its execution, neither in the kernel nor in user space. To force the usage of locking mechanisms, two _pi_ tasks are executed in parallel, making concurrent _read()_ operations, causing contention in the dispute of the lock. Different mutual exclusion mechanisms can be used in the module. In the following examples, both spinlock and RT Mutex were used.

> 该任务无自愿暂停执行，既不在内核中也没有在用户空间中执行。为了强制使用锁定机制，并行执行两个 _pi_ 任务，并并发*read()*操作，从而导致锁定争议。可以在模块中使用不同的相互排除机制。在以下示例中，使用了 Spinlock 和 RT Mutex。

The IRQ handlers of the experimental system were also used for the characterization of this kind of tasks.

> 实验系统的 IRQ 处理程序也用于表征此类任务。

## 5.1 _Characterization of the interrupt handlers timeline_

> ## 5.1 _中断处理器的 characterization timeline _

The following trace shows the execution of a local timer interrupt. To make the trace output clear, the trace entries that did not affect the timing characteristic of the task have been replaced by _. . . _.

> 以下跟踪显示了当地计时器中断的执行。为了使跟踪输出清晰，不影响任务正时特征的跟踪条目已被*替换。。。*。

<img src="./media/image26.png" style="width:5.55706in;height:0.65104in" />

During its execution, task _pi_ calls the function _raw_spinlock_irqsave()_, disabling interrupts. The interrupts are then enabled in the unlock operation, performed by function _raw_spin_unlock_irqrestore()_. In the earlier trace, while releasing the _raw_spinlock()_ at line 1, interrupts are enabled at line 3, and the processor starts executing the _timer_ interrupt handler, which is carried out by the function _smp_apic_timer_interrupt()_, at line 5.

> 在执行过程中，任务 _pi_ 调用函数 _raw_spinlock_irqsave()_，禁用中断。然后在解锁操作中启用中断，由函数 _raw_spin_unlock_irqrestore()_ \_ \_ \_ *。在较早的跟踪中，在第 1 行释放\_raw_spinlock()*时，在第 3 行中启用了中断，并且处理器开始执行* timer* interrupt 处理程序，该函数由函数 _smp_apic_apic_timer_interrupp()_，在第 5 行中进行。

In this case, it is possible to affirm that the interrupt handler was delayed. However, the interrupt may have occurred at any time during the interrupt-disabled section. Thus, it is not possible to exactly determine the release jitter. Nevertheless, it is safe to assume the worst case: that the interrupt occurred shortly after task _pi_ disabled interrupts.

> 在这种情况下，有可能确认中断处理程序被延迟。但是，中断可能是在中断可分配部分期间的任何时候发生的。因此，不可能准确地确定释放抖动。然而，可以安全地假设最坏的情况：中断发生在任务 _pi_ 禁用中断后不久。

![](./media/image27.png)

Continuing the execution, the interrupt handler executes _\_raw_spin_lock_irqsave()_ at line 4, which would disable interrupts. However, because interrupts are disabled by the processor itself when calling an interrupt handler, the trace identifies that interrupts are already disabled and does not print the line reporting the state change of interrupts.

> 继续执行，中断处理程序执行* \ * raw*spin_lock_irqsave()*在第 4 行，这将禁用中断。但是，由于处理器本身在调用中断处理程序时被打断，因此痕迹标识了中断已经被禁用，并且没有打印出报告中断状态变化的行。

![](./media/image30.png)

The interrupt handler wakes up the _timer softirq_ at line 8 and finishes its execution returning control to the previous task.

> 中断处理程序在第 8 行唤醒了 _timer softirq_，并完成其执行控制权的执行控制。

<img src="./media/image32.png" style="width:5.59998in;height:0.27083in" />

Finally, control is returned to the task _pi_, which continues the releasing of the _raw_spinlock()_, enabling preemptions, and then returning.

> 最后，将控件返回到任务 _pi_，该任务继续释放 _raw_spinlock()_，启用先发，然后返回。

In general, it can be said that an interrupt handler may be delayed whenever interrupts are disabled. It is noteworthy that in addition to the interrupt control carried out by the operating system, the processor architecture also defines its rules for masking interrupts. The points at which the processor disables interrupts are beyond the control of the operating system. For this reason, it is not possible to trace these points. Thus, for each hardware architecture, we must identify the points at which the hardware disables interrupts itself.

> 通常，可以说，每当打断中断时，中断处理程序都可能会延迟。值得注意的是，除了操作系统进行的中断控制外，处理器体系结构还定义了其掩盖中断的规则。处理器禁用中断的点超出了操作系统的控制。因此，不可能追踪这些要点。因此，对于每个硬件体系结构，我们必须确定硬件禁用自身的点。

Regarding the ability of interrupts to interfere with the execution of other interrupts, we consider that a maskable interrupt can be interrupted by an NMI and that an NMI blocks other NMIs [34](#_bookmark64).

> 关于中断干扰其他中断执行的能力，我们认为可掩盖的中断可以被 NMI 中断，并且 NMI 阻止了其他 NMI [34](#\_ bookmark64)。

### 5.1.1 _Interrupt handlers timeline._

> ### 5.1.1 \_ interrupt 处理者时间表。

From the analysis of the trace of several executions, and based on the mapping of abstractions from Section [2](#_bookmark0), it was possible to characterize the execution of interrupt handlers. However, because of the different restrictions imposed to maskable and NMIs, it was necessary to characterize the interrupts for these two different modes.

> 根据对几个执行的痕迹的分析，以及基于[2](#\_ bookmark0)节的抽象映射的映射，可以表征中断处理程序的执行。但是，由于对可掩盖和 NMI 的限制有所不同，因此有必要表征这两种不同模式的中断。

An NMI can be enabled at any time and therefore must obey a set of very strict rules. For example, an NMI handler cannot use mutual exclusion mechanisms, except when it is used only in this context, for synchronization with other NMIs running on another CPU. The code of NMI handlers cannot be reentrant; that is, a second NMI will not be handled during the execution of an NMI [34](#_bookmark64).

> 可以随时启用 NMI，因此必须遵守一组非常严格的规则。例如，NMI 处理程序不能使用相互排除机制，除非仅在此上下文中使用它与在另一个 CPU 上运行的其他 NMI 同步。NMI 处理程序的代码不能重新进入；也就是说，在执行 NMI [34](#\_ bookmark64)时，将不会处理第二个 NMI。

From these restrictions and the trace of interrupts, it is possible to characterize the execution of NMIs as in Figure [3](#_bookmark13).

> 从这些限制和中断的痕迹中，可以像图[3](#\_ bookmark13)中表征 NMI 的执行。

For NMIs, the response time _R$i$_ is given by the delay between the IRQ activation and the return of the NMI handler. The release jitter _J$i$_ will occur if the system is already handling an NMI. In this case, it is safe to assume the worst case: that the second NMI was activated right after the first NMI was activated.

> 对于 NMI，响应时间*r $ i $ *由 IRQ 激活与 NMI 处理程序的返回之间的延迟给出。如果系统已经在处理 NMI，则发行抖动* j $ i $ *将会发生。在这种情况下，可以肯定地假设最坏的情况：第二个 NMI 在激活第一个 NMI 后立即激活。

![](./media/image33.png)

Figure 3. <span id="_bookmark13" class="anchor"></span>Non-maskable interruption timeline. IRQ, interrupt request.

> 图 3. <span ID =“ \_ bookmark13” class =“锚”> </span>不掩盖的中断时间表。IRQ，中断请求。

![](./media/image43.png)

Figure 4. <span id="_bookmark14" class="anchor"></span>Maskable interruption timeline. IRQ, interrupt request.

> 图 4. <span ID =“ \_ bookmark14” class =“锚”> </span>可掩盖的中断时间表。IRQ，中断请求。

The busy window _W$i$_ is defined as the time that the NMI held the CPU during its execution, being determined by the time interval between the call and the return of the IRQ handler. The blocking represented by variable _B$i$_ must be implemented as busy waiting, which should occur only for synchronization between NMIs. Finally, the runtime _S$i$_ is determined by the busy window, discounting the time that the NMI may have been blocked by another NMI.

> 繁忙的窗口*W $ i $ *定义为 NMI 在执行过程中持有 CPU 的时间，由呼叫和 IRQ 处理程序返回之间的时间间隔确定。由变量* b $ i $ *表示的阻止必须作为忙碌的等待实现，这仅在 NMIS 之间同步。最后，运行时* s $ i $ *由繁忙的窗口确定，折价 NMI 可能已被另一个 NMI 阻止的时间。

Nevertheless, there is one exception to this rule, which occurs because of the execution of the instruction _iret_ during the execution of an NMI handler, usually called by the code of another interrupt handler inside the NMI, that is, the page-fault handler. This exception is known as _iret flaw_ [34](#_bookmark64) and allows the nesting of this class of interrupt handlers. For NMI handlers subject to this exception, the characterization of its execution is the same of maskable interrupt handlers.

> 然而，此规则有一个例外，这是由于执行指令 _iret_ 在执行 NMI 处理程序时发生的，通常由 NMI 内部的另一个中断处理程序的代码调用，即页面错误处理程序。此例外被称为 _iret flaw_ [34](#\_ bookmark64)，并允许此类中断处理程序的嵌套。对于符合此例外的 NMI 处理程序，其执行的表征与可掩盖的中断处理程序相同。

On the other hand, the maskable interrupt may suffer interference from NMI; hence, its characterization differs from the NMI. As the NMIs handlers may execute at any time, it is assumed here that they have a higher priority than the maskable interrupt handlers. The same applies for the NMI handlers subject to _iret flaw_.

> 另一方面，可掩盖的中断可能会受到 NMI 的干扰。因此，其表征与 NMI 不同。由于 NMIS 处理程序可以随时执行，因此在这里假定他们的优先级高于可掩盖的中断处理程序。符合\_iret 缺陷的 NMI 处理程序也是如此。

The characterization of the maskable interrupt handlers is shown in Figure [4](#_bookmark14).

> 可掩盖的中断处理程序的表征如图[4](#\_ bookmark14)所示。

For maskable interrupts, the response time _R$i$_ is determined by the time interval between the activation and the return of the interrupt handler. The release jitter _J$i$_ can happen if the system has interrupts disabled, either by an action of the operating system or by action of the processor itself, for example, if it is already handling an interrupt. In this case, it is safe to assume that in the worst case, activation took place immediately after the disabling of interrupts.

> 对于可掩盖的中断，响应时间*r $ i $ *由激活和返回中断处理程序的返回之间的时间间隔确定。如果系统通过操作系统的操作或处理器本身的操作，如果系统已被禁用，则会发生抖动抖动* j $ i $ *，例如，如果它已经在处理中断。在这种情况下，可以肯定地假设在最坏的情况下，激活发生在破坏中断后立即进行。

Differently from NMIs, maskable interrupts can suffer interference _I$i$_ , caused by the occurrence of an NMI. The busy window _W$i$_ is defined as the time that the interruption held the CPU during its execution, being determined by the time interval from start to finish of the interrupt handler. Blocking _B$i$_ is always implemented as busy waiting. Lastly, the runtime _S$i$_ is determined by the busy window discounting blocking and interference from other interrupt handlers.

> 与 NMI 的不同，可掩盖的中断可能会遭受干扰*i $ $ * $ _ $ _ $ *，这是由于 NMI 的出现而引起的。繁忙的窗口\_W $ i $ *定义为中断在执行过程中保存 CPU 的时间，由中间处理程序的开始间隔确定。阻止* b $ i $ *始终将其实现为忙碌的等待。最后，运行时* s $ i $ *是由繁忙的窗口折扣阻止和其他中断处理程序的干扰确定的。

## 5.2. _Characterization of the threads timeline_

> ## 5.2。_线程时间表的表征_

In order to characterize the execution of a real-time thread, we used task _pi_. The C code of its main execution loop is shown as follows:

> 为了表征实时线程的执行，我们使用了任务 _pi_。其主要执行循环的 C 代码如下：

<img src="./media/image53.png" style="width:0.83448in;height:0.16844in" />
<img src="./media/image54.png" style="width:1.91659in;height:0.16667in" />

Inside the infinite loop created with _for_, the function _pause()_ suspends the task execution, waiting for a new activation. A periodic timer signal wakes up the task, starting a new activation. Returning to execution, the job executes the system call _read()_, activating the module into the kernel, which will run the busy waiting protected by a mutex variable. After return from _read()_, the task finishes its activation by suspending itself and waiting for a new activation.

> 在使用 _FOR_ 创建的无限循环中，函数 *pause()*暂停任务执行，等待新的激活。周期性计时器信号唤醒了任务，开始新的激活。返回执行后，作业执行系统呼叫* read()*，将模块激活到内核中，该模块将运行由 MUTEX 变量保护的繁忙等待。从*read()*返回后，任务通过暂停并等待新的激活来完成激活。

### 5.2.1 _Trace of a thread execution._

> ### 5.2.1 _ trace execution._

The following trace shows an activation of the _pi_ task, in which it runs without suffering blocking or interference.

> 以下跟踪显示了 _pi_ 任务的激活，其中它在其中运行而不会遭受阻塞或干扰。

![](./media/image55.png)

The timer _softirq_ that will activate task _pi_, before activating it at line 2, migrates it to CPU 0 at line 1. CPU 0 is on _idle_ state, which disables preemption. When CPU 0 receives the event that a task has been activated, it leaves the _idle_ state and then enables preemption. After enabling preemption, the scheduler is called and performs a context switch to task _pi_.

> 计时器 _softirq_ 将激活任务 _pi_，然后在第 2 行激活它之前，将其迁移到第 1 行中的 CPU 0，CPU 0 在 _idle_ 状态下，该 cpu cpu nate on _idle_ state，它禁用了 preekention。当 CPU 0 接收到已激活任务的事件时，它会离开 _idle_ 状态，然后启用先发。在启用抢占后，调用调度程序并执行上下文切换到任务 _pi_。

![](./media/image57.png)

Once activated, the scheduler that puts the task to sleep resumes its execution at line 12, returning the execution of system call _pause()_ at line 13. On the return of _pause()_ to user space, the functions that handle the timer signal are called; these functions are _do_notify_resume()_ and _sys_rt_sigreturn()_, between lines 16 and 27. Despite not appearing in the task’s code, these functions are performed by the C library, as part of the implementation of signal handling.

> 激活后，将任务放置的调度程序在第 12 行中恢复其执行，返回系统呼叫的执行 *pause()*在第 13 行。信号被调用；这些功能是* do_notify_resume()*和* sys_rt_sigreturn()*，在第 16 和 27 行之间。尽管未出现在任务的代码中，但这些功能是由 C 库执行的，作为信号处理的实现的一部分。

![](./media/image62.png)
![](./media/image64.png)
![](./media/image65.png)

Figure 5. <span id="_bookmark15" class="anchor"></span>Real-time thread.

> 图 5. <span ID =“ \_ bookmark15” class =“锚”> </span>实时线程。

At line 30, the function _read()_ is performed. It obtains access to the critical section at line 35, and does some busy waiting. After finishing the busy waiting, it releases the _raw_spinlock()_ at line 38, returning to user space at line 43.

> 在第 30 行，执行函数 _read()_。它在第 35 行中获得了对关键部分的访问权限，并进行了一些忙碌的等待。完成忙碌的等待后，它将在第 38 行中发布 _raw_spinlock()_，并在第 43 行返回用户空间。

<img src="./media/image74.png" style="width:5.60128in;height:0.84896in" />

After returning, task _pi_ calls function _pause()_ at line 45, finishing the activation while leaving the CPU at state _S_ (line 47).

> 返回后，任务 _pi_ 调用函数 *pause()*在第 45 行，完成激活，同时在状态* s*(第 47 行)中离开 CPU。

### 5.2.2 _Characterization of the threads timeline._

> ### 5.2.2 \_线程时间表的 characterization。

The characterization of real-time threads is more complex than that of the interrupt handlers. Therefore, it was made in parts. Firstly, we considered an activation without blocking and interference. Then, we identified the different forms of blocking and interference, showing how they can affect the real-time threads timing behavior. Figure [5](#_bookmark15) describes the execution of a real-time thread without interference or blocking.

> 实时线程的表征比中断处理程序的表征更为复杂。因此，它是部分制作的。首先，我们考虑了一种激活而没有阻塞和干扰。然后，我们确定了阻塞和干扰的不同形式，显示了它们如何影响实时线程的时序行为。图[5](#\_ bookmark15)描述了无干扰或阻塞的实时线程的执行。

For threads, the response time _R$i$_ is the time between the thread activation by the event sched*wakeup and the context switch when the thread leaves the processor, suspending its execution in state \_S*. The busy window _W$i$_ is the time interval between the first context switch after the task’s activation and the context switch in which the task leaves the processor to sleep, finishing its execution. The release jitter _J$i$_ can be associated with two reasons: preemption or interrupts being disabled by a process of lower priority and by a scheduler execution that removes the current task. Both must happen at the processor on which the task was activated.

> 对于线程，响应时间 *r $ i $ *是事件计划*唤醒线程激活与线程离开处理器时的上下文开关之间的时间，并将其在状态\ \_s*中暂停执行。繁忙的窗口*W $ i $ *是任务激活后第一个上下文开关与任务使处理器入睡的上下文开关之间的时间间隔，完成了执行。发行抖动* j $ i $ *可以与两个原因相关联：通过较低的优先级过程以及通过删除当前任务的调度程序执行程序被禁用或中断。两者都必须发生在激活任务的处理器上。

After a task starts its execution, the scheduling routine that had suspended that task runs until it returns to the application code. Unlike most response-time analyses, where the scheduling overhead is considered negligible, with Linux, this overhead is important and should be measured. It was necessary to create a new abstraction to accommodate this overhead, which was denominated as scheduling overhead. This abstraction is associated with the variable _SS$i$_ , comprising the exitscheduling overhead, that is, the time between the calling of function _schedule()_ and the context switch; and the entry-scheduling overhead, that is, the time between the context switch and the return of function _schedule()_.

> 任务开始执行后，暂停该任务的计划例程直到返回应用程序代码为止。与大多数响应时间分析不同，在 Linux 使用 Linux 的情况下，调度开销可忽略不计，该开销很重要，应测量。有必要创建一个新的抽象来容纳这个开销，该开销被称为安排开销。此抽象与变量 *ss $ i $ *相关，包括 exitscheduling 开销，即函数呼叫* schedule()*和上下文开关之间的时间；和入口安排开销，即上下文开关与函数返回之间的时间* schedule()*。

Finally, the computation time _S$i$_ is the time that the thread has executed its own code, which can be either in user space or kernel space, excluding scheduling overhead, blocking, and interference.

> 最后，计算时间*s $ i $ *是线程执行自己的代码的时间，该代码可以在用户空间或内核空间中，不包括计划开销，阻止和干扰。

Regarding the interference _I$i$_ , Figure [6](#_bookmark16) describes the two forms of interference that a task can suffer: interference from an interrupt handler and interference from a thread.

> 关于干扰*i $ i $ *，图[6](#\_ bookmark16)描述了任务可能会遭受的两种干扰形式：中断处理程序的干扰和线程的干扰。

Because the interrupt handlers are activated by the hardware, they do not need to be scheduled. The interference of an interrupt handler is given by the busy window _W$i$_ of the interrupt handler.

> 由于中断处理程序被硬件激活，因此无需安排它们。中断处理程序的干扰是由繁忙的窗口*W $ i $ *给出的中断处理程序。

Differently from the interference of interrupt handlers, the interference caused by threads adds scheduling overhead to the current running task. This overhead increases the task’s own scheduling overhead. The interference of a high-priority thread is given by the time interval between the context switch that removes the current thread from the processor and the context switch that gives back the processor to the thread. It is possible to identify whether a thread is suffering interference by the state that it is leaving the processor. When a real-time thread leaves the processor in _R_ state, it is suffering interference.

> 与中断处理程序的干扰不同，线程引起的干扰将计划开销添加到当前运行任务中。这个间接费用增加了任务自己的安排开销。高优先级线程的干扰是由从处理器中删除当前线程的上下文开关之间的时间间隔给出的，从而将处理器还给线程的上下文开关。可以确定线程是否正在遭受国家离开处理器的干扰。当实时线程将处理器留在 _r_ 状态下时，它会遭受干扰。

![](./media/image75.png)
![](./media/image76.png)
![](./media/image81.png)
![](./media/image82.png)
![](./media/image83.png)
![](./media/image84.png)

Figure 6. <span id="_bookmark16" class="anchor"></span>Forms of thread interference.

> 图 6. <span ID =“ \_ bookmark16” class =“锚”> </span>线程干扰的形式。

![](./media/image89.png)
![](./media/image93.png)
![](./media/image95.png)
![](./media/image96.png)
![](./media/image97.png)

Figure 7. <span id="_bookmark17" class="anchor"></span>Forms of thread blocking.

> 图 7. <span ID =“ \_ bookmark17” class =“锚”> </span>线程阻塞的形式。

Regarding locks, one thread can experience two forms of blocking: implemented as busy waiting or implemented by suspending the execution of the thread. Figure [7](#_bookmark17) demonstrates both cases.

> 关于锁，一个线程可以体验两种形式的阻塞：通过暂停线程的执行而忙于等待或实现。图[7](#\_ bookmark17)证明了这两种情况。

The first example of _B$i$_ is a busy-waiting lock, where the task keeps running on its context, until the lock is released by another thread. In the trace, it is possible to identify this blocking by the tracepoint _lock_contended_. After acquiring access to the critical section, tracepoint _lock_acquired_ is shown. Thus, the blocking time is given by the time interval between these two tracepoints.

> *b $ i $ *的第一个示例是一个忙碌的锁定锁，该任务在其上下文上一直在运行，直到另一个线程释放锁。在跟踪中，可以通过跟踪点* lock_contended*识别此阻止。获取对关键部分的访问后，显示 TracePoint _lock_acquired_。因此，阻止时间由这两个痕迹之间的时间间隔给出。

The second example is the type of blocking that suspends the thread’s execution until it acquires the critical section. In this case, as the scheduling overhead happens because of the mutual exclusion mechanism, it is considered that this time is part of the task’s blocking time, and the measurement is made in a manner analogous to the mechanisms that do not suspend execution: the time interval between tracepoints _lock_contended_ and _lock_acquired_.

> 第二个示例是暂停线程执行的阻止类型，直到获得关键部分为止。在这种情况下，由于调度开销是由于相互排除机制而发生的，因此认为这次是任务阻止时间的一部分，并且测量以类似于不暂停执行的机制的方式进行。跟踪点之间的间隔 _lock_contended_ 和 _lock_acquired_。

# 6. USING TIMEFLOW TO MEASURE TIMING PROPERTIES

> ＃6.使用时流来测量正时属性

Based upon the characterization of the execution of real-time tasks on Linux, the following sections show examples of trace and their interpretation, that is, how the value of each real-time abstraction can be collected and evaluated. It is noteworthy that it is not one objective of this article to determine the worst case of any of the real-time abstractions presented. But only to identify the variables and to define how to compute them. Empirical determination of maximum execution times requires many billions of runs. For instance, the Open Source Automation Development Lab [35](#_bookmark65) carries out multi-year latency testing on a number of versions of the PREEMPT RT Linux kernel on a variety of hardware.

> 基于在 Linux 上实时任务执行的表征，以下各节显示了迹线及其解释的示例，即如何收集和评估每个实时抽象的价值。值得注意的是，确定提出的任何实时抽象的最坏情况并不是本文的一个目标。但仅是为了识别变量并定义如何计算它们。最大执行时间的经验确定需要数十亿美元的运行。例如，开源自动化开发实验室[35](#\_ bookmark65)在多种硬件上对许多版本的 RT Linux 内核进行了多年延迟测试。

The value for the abstractions presented in the next sections is defined for the described activation and does not represents the worst-case values, for both task and system. We start with an example of activation without blocking and interference, which is followed by an example of activation with the occurrence of blocking.

> 为所描述的激活定义了下一个部分中介绍的抽象值的值，并且不代表任务和系统的最坏情况值。我们从激活的示例开始，而无需阻塞和干扰，其次是激活的示例，并以阻塞的发生。

## 6.1 _Activation without concurrence_

> ## 6.1 * contrence *的激活\_

The first example is an execution without blocking and interference from higher-priority threads. The trace output is the following.

> 第一个示例是执行，而不会阻止和干扰更高优率线程。跟踪输出为以下。

![](./media/image102.png)

Line 1 shows the instant of time when task _pi_-838 is awakened on CPU 0, which was in the _idle_ state. Preemption is enabled at line 2, followed by the scheduler execution at line 3. Line 4 shows the event of context switch to task _pi-838_. With these trace points, it is possible to state that the release of this job was delayed by the preemption and scheduling routine. Considering the release jitter as the time between the activation and the context switch, _J$pi$_$—_838_$ equals to 21.864 *K*s.

> 第 1 行显示了任务 _pi_-838 在 cpu 0 上唤醒的时间的瞬间，该 cpu 0 处于 _idle_ 状态。在第 2 行中启用了抢先，然后在第 3 行进行了调度程序执行。第 4 行显示了上下文切换到任务 _PI-838_ 的事件。有了这些痕量点，有可能声明该作业的释放被抢先和调度例程延迟。将发布抖动视为激活和上下文开关之间的时间，_j $ pi $ _ $ - _ 838_ $等于 21.864 *k *s。

<img src="./media/image104.png" style="width:1.65538in" />
<img src="./media/image105.png" style="width:4.0533in;height:0.26562in" />

After the context switch, the scheduling routine returns at line 5, thus starting the execution of application code. Considering the scheduling overhead as the time interval between the context switch and the return of the _schedule()_ function, the schedule overhead _SS$pi$_$—_838_$ is 4.124 *K*s.

> 上下文开关后，调度例程在第 5 行返回，从而启动应用程序代码的执行。将调度开销视为上下文开关之间的时间间隔和*schedule()*函数的返回，时间表开销* ss $ pi $ * $ _ $ -_ 838\_ $ is 4.124 *k *s。

![](./media/image106.png)
![](./media/image111.png)
![](./media/image112.png)
![](./media/image113.png)
![](./media/image116.png)
![](./media/image117.png)
![](./media/image118.png)

Figure 8. <span id="_bookmark19" class="anchor"></span>Timeline of a job without concurrence.

> 图 8. <span ID =“ \_ bookmark19” class =“锚”> </span>作业的时间表而无需并发。

Table II. <span id="_bookmark20" class="anchor"></span>Real-time tasks setup.

> 表 II。<span ID =“ \_ bookmark20” class =“锚”> </span>实时任务设置。

Throughout the execution, the task has not suffered blocking or interference. At line 36, it can be seen that the thread left the CPU in the _S_ state. So it is possible to affirm that the task finished its activation.

> 在整个执行过程中，任务尚未遭受阻塞或干扰。在第 36 行，可以看出线程将 CPU 留在 _s_ 状态下。因此，可以肯定该任务完成了激活。

The scheduling overhead of removing the thread from the processor is the time interval between the call to _schedule()_ at line 35 and the context switch at line 36, and it was 10.654 *K*s. By summing the scheduler overhead at the starting and the finishing of the execution, the scheduler overhead contributed with 14.778 *K*s to the response time.

> 从处理器中删除线程的计划开销是呼叫*schedule()*在第 35 行和第 36 行的上下文开关之间的时间间隔，为 10.654 *k *s。通过将调度程序的开销概括为在执行的起点和完成时，调度程序的开销贡献了 14.778 *k *s，以响应时间。

The context switch at line 36 is also used to calculate the response time, which is the time difference between this line and the activation of the task at line 1. The response time _R$pi$_$—_838_$ is 100.149 *K*s.

> 第 36 行的上下文开关还用于计算响应时间，这是该行之间的时间差与第 1 行的激活之间的时间差。响应时间*r $ pi $ * $ - _ 838_ $ is 100.149 *k *s。

Furthermore, it is possible to define the busy period as the time interval between both context switches at lines 4 and 36, so _W$pi$_$—_838_$ is 78.285 *K*s.

> 此外，可以将繁忙周期定义为第 4 和 36 行的上下文开关之间的时间间隔，因此*W $ pi $ * $ - _ 838_ $ is 78.285 *k *s。

Finally, the execution time _S$pi$_$—_838_$ of this activation is defined as the response time _R$pi$_$—_838_$ minus the release jitter _J$pi$_$—_838_$ and the sum of the scheduler overhead _SS$pi$_$—_838_$. Thus, _S$pi$_$—_838_$ = _l00.l49_ — _2l.864_ — _l4.778_ = *63.507 K*s

> 最后，执行时间 _s $ pi $ _ $ - _ 838_ $的激活定义为响应时间 *r $ pi $ * $ _ $ - _ 838* $减去发行抖动\_j $ pi $ * $ _ $ - _ 838* $和调度程序间接费用\_ss $ pi $ * $ - _ 838_ $。因此，_s $ pi $ _ $ - _ 838_ $ = _l00.l49_ - _2l.864_ - _l4.778_ = *63.507 k *s

With the definition of these variables, it is possible to show the timeline of this job graphically, similar to that used in the real-time systems literature. Figure [8](#_bookmark19) shows this timeline.

> 通过这些变量的定义，可以以图形方式显示该作业的时间表，类似于实时系统文献中使用的时间。图[8](#\_ Bookmark19)显示了此时间表。

## 6.2 _Concurrent activation_

> ## 6.2 _ Concurrent 激活_

The next example shows the execution of two _pi_ tasks. These tasks have the configuration described in Table [II](#_bookmark20). Task _pi-839_ is the high-priority task, and _pi-838_ is the low-priority task.

> 下一个示例显示了两个 _pi_ 任务的执行。这些任务具有表[II](#* Bookmark20)中描述的配置。任务\_pi-839*是高优先级任务，_pi-838_ 是低优先级任务。

These two tasks will compete for the critical section protected by a Mutex RT. The events in the trace will be described in the same order they appear.

> 这两个任务将争夺由静音 RT 保护的关键部分。痕迹中的事件将以相同的顺序描述。

<img src="./media/image123.png" style="width:5.52355in;height:0.36979in" />

Lines 1 and 2 show the activation of the low-priority and high-priority tasks, respectively.

> 第 1 行和第 2 行分别显示了低优先级和高优先级任务的激活。

<img src="./media/image124.png" style="width:5.48787in;height:0.55729in" />

After enabling preemption, CPU 4 exits from _idle_ and calls the scheduler, changing the context to task _pi-838_, which has low priority. By considering the time interval between context switch and the sched wakeup events at lines 3 and 1, it is possible to define the release jitter _J$pi$_$—_838_$ as 63.586 *K*s.

> 在启用抢占之后，CPU 4 从 _idle_ 退出并调用调度程序，将上下文更改为任务 _PI-838_，其优先级较低。通过考虑上下文开关与第 3 行的 Sched Wakeup 事件之间的时间间隔，可以定义释放抖动*j $ pi $ * $ -_ 838_ $ as 63.586 *k *s。

![](./media/image125.png)

After the context switch, the scheduler returns the execution control to the lowpriority task. The schedule overhead is defined by the time interval between the return of the scheduling routine and the context switch at lines 9 and 5, respectively. The scheduling overhead _SS$pi$_$—_838_$ is 6.565 *K*s.

> 上下文开关后，调度程序将执行控件返回到低优先级任务。时间表开销是由计划例程的返回与第 9 行的上下文开关之间的时间间隔定义。调度开销*ss $ pi $ * $ - _ 838_ $是 6.565 *k *s。

Once task execution is resumed, the low-priority task starts the processing of the signals responsible for its activation.

> 恢复任务执行后，低优先级任务将开始处理负责其激活的信号。

<img src="./media/image127.png" style="width:5.54019in;height:0.55729in" />

The behavior of the high-priority task is similar to that of the low-priority task. Preemption is enabled on CPU 5 exiting from _idle_, then the scheduler is called to perform the context switch to the high-priority task _pi-839_. Thus, it is possible to define the release jitter _J$pi$_$—_839_$ as 64.574 *K*s.

> 高优先级任务的行为类似于低优先级任务的行为。从 _idle_ 退出的 CPU 5 上启用了抢先，然后调用调度程序执行上下文切换到高优先级任务 _PI-839_。因此，可以定义发行抖动*j $ pi $ * $ - _ 839_ $ as 64.574 *k *s。

![](./media/image128.png)

Once it acquired the processor, the high-priority task returns from the scheduler and starts its execution. On this activation, the job suffered 6.068 *K*s of scheduling overhead, which is the time interval between the events at lines 20 and 16.

> 一旦获得处理器，高优先级任务就会从调度程序返回并开始执行。在此激活中，该作业遭受了调度开销的 6.068 *k *s，这是第 20 和 16 行的事件之间的时间间隔。

<img src="./media/image130.png" style="width:4.43707in;height:0.94271in" />

At this point, both tasks are running the handlers of the signals that activated them.

> 在这一点上，这两个任务都在运行激活它们的信号的处理程序。

![](./media/image131.png)

While the low-priority task executes the _write()_ system call at line 34, the high-priority task is still handling a signal at line 36. At line 38, the low-priority task calls function _mutex_lock()_ for the RT mutex. This task then acquires the lock without contention, returning to execution at line 42.

> 当低优先级任务执行 *write()*在第 34 行的系统调用时，高优先级任务仍在第 36 行中处理信号。在第 38 行，低优先级任务调用函数* mutex_lock()* for RT 静音。然后，此任务无需争夺即可获取锁，并在第 42 行中返回执行。

<img src="./media/image134.png" style="width:5.53058in;height:0.9375in" />

At line 46, the high-priority task executes the _write()_ system call and then tries to acquire the mutex. However, as the low-priority task is in its critical section, the high-priority task suffers contention at line 50, starting a blocking interval.

> 在第 46 行，高优先级任务执行*write()*系统调用，然后尝试获取 MUTEX。但是，由于低优先级的任务在其关键部分中，因此高优先级任务在第 50 行中遭受争夺，开始阻止间隔。

<img src="./media/image135.png" style="width:5.57073in;height:0.35937in" />

At line 53, the high-priority task activates the mechanism of priority inheritance, assigning its priority to the low-priority task.

> 在第 53 行，高优先级任务激活了优先级继承的机制，将其优先级分配给了低优先级任务。

<img src="./media/image136.png" style="width:5.54795in;height:0.84896in" />

After finishing the execution of the priority inheritance protocol, the high-priority task changes its state to sleeping on uninterruptible mode (_D state_) and then calls the scheduler causing the context switch at lines 55 and 56.

> 在完成优先级继承协议的执行后，高优先级任务将其状态更改为在不间断模式(_D state_)上睡觉，然后调用调度程序，导致第 55 和 56 行的上下文开关。

<img src="./media/image137.png" style="width:5.54098in;height:1.04167in" />

After finishing the execution of its critical section, the low-priority task calls the function that releases the mutex at line 57. It is worth noticing that the low-priority task is still running with high priority at this moment. While releasing the mutex, the high-priority task is awakened at line 61. Finally, the low-priority task returns to its original priority at line 62.

> 在完成其关键部分的执行后，低优先级任务调用了在第 57 行中释放静音的功能。值得注意的是，低优先级任务目前仍在优先级。在释放静音的同时，在第 61 行中唤醒了高优先级的任务。最后，低优先级任务恢复到第 62 行的原始优先级。

![](./media/image138.png)

Exiting from idle, CPU 1 enables preemptions at line 63. Furthermore, it calls the scheduler at line 64, executing the context switch at line 65.

> 从空闲中退出，CPU 1 可以在第 6 行上的先发。此外，它在第 64 行中调用调度程序，在第 65 行中执行上下文开关。

![](./media/image140.png)

After finishing the release of the mutex, the low-priority task resumes its execution. It is worth noticing that the lock release of the RT mutex added 73.306 *K*s of overhead to the low-priority task, which is a relatively large time, considering that this task should complete in just over 100 *K*s if no RT Mutex release was required. This overhead is the reason for the common suggestion to use spinlocks in short critical sections [15](#_bookmark46).

> 完成静音的释放后，低优先级任务恢复了其执行。值得注意的是，RT Mutex 的锁定释放添加了 73.306 *k *s 开销到低优先级任务，这是一个相对较大的时间，考虑到此任务应在 100 *k *中完成，如果没有。需要 RT MUTEX 释放。该开销是在简短的临界部分中使用 Spinlock 的常见建议[15](#\_ bookmark46)。

<img src="./media/image142.png" style="width:4.00364in;height:0.45833in" />

After releasing the mutex, the low-priority task returns to user space. All in all, the system call _read()_ took 183.593 *K*s. Much of this time has come from the release of the mutex. At this point, the low-priority task calls the scheduler at line 78.

> 释放静音后，低优先级任务返回到用户空间。总而言之，系统调用*read()*取 183.593 *k *s。这次的大部分时间都来自静音的发行。在这一点上，低优先级任务在第 78 行中调用调度程序。

![](./media/image143.png)

The high-priority task, after being scheduled, returns to the acquisition of RT Mutex. Its blocking time is the time interval between the event that signals the acquisition of the mutex at line 82 and the task trying to acquire the mutex at line 49. There is a blocking time _B$pi$_$—_839_$ of 178.545 *K*s.

> 安排后，高优先级任务返回到 RT Mutex 的收购。它的阻止时间是事件之间的时间间隔，该事件指示在第 82 行中获取静音的时间与试图在第 49 行获取 MUTEX 的任务。有一个阻止时间*b $ pi $ * $ _ $ _ $ -_ 839_ $ 178.545 *k*s。

<img src="./media/image145.png" style="width:4.29498in" />

After finishing the critical section, the high-priority task initiates the release of the mutex.

> 完成关键部分后，高优先级任务启动了静音的释放。

<img src="./media/image146.png" style="width:5.4763in;height:0.46354in" />
![](./media/image147.png)

The low-priority task, after calling the scheduler at line 78, completes the process of leaving the CPU by running the context switch. Once we came to the end of the execution, it is possible to set the value for the other variables, starting with the scheduling overhead.

> 低优先级任务在第 78 行调用调度程序后，通过运行上下文开关来完成离开 CPU 的过程。一旦我们到达执行的末尾，就可以从计划开销开始，设置其他变量的值。

The overhead of the scheduling operation that removed the task from the CPU is the time interval between the scheduler being activated at line 78 and the context switch at line 84. This time interval was 15,399 *K*s. The trace shows then a total scheduling overhead of 21.964 *K*s

> 从 CPU 中删除任务的调度操作的开销是在第 78 行激活的调度程序与第 84 行的上下文开关之间的时间间隔。此时间间隔为 15,399 *k *s。跟踪显示然后总的调度开销为 21.964 *k *s

The busy window _W$pi$_$—_838_$ of this task activation is the time interval between the task starting and finishing its execution. This value can be computed as the time interval between the context switches at lines 5 and 84, respectively, resulting in a _W$pi$_$—_838_$ of 302.040 *K*s.

> 繁忙的窗口*W $ pi $ * $ - * 838*此任务激活是任务启动和完成执行之间的时间间隔。该值可以分别计算为第 5 行和 84 行之间的上下文开关之间的时间间隔，从而导致*W $ pi $ * $ - _ 838_ $ 302.040 *k *s。

The response time of this activation of _R$pi$_$—_838_$ is 365.626 *K*s. It is given by the time interval between the event that activated the task at line 1 and the event that finished the activation of the task at line 84.

> _r $ pi $ _ $ - _ 838_ $的响应时间是 365.626 *k *s。它是通过在第 1 行中激活任务的事件之间的时间间隔和完成任务在第 84 行激活的事件给出的。

This activation of the task showed no blocking or interferences. One can estimate its execution time from its response time minus the activation delay and scheduling overheads: _S$pi$_$—_838_$ = _365.626_ — _63.586_ — _2l.964_ = *280.076 K*s

> 任务的激活没有显示阻塞或干扰。可以从响应时间估算其执行时间减去激活延迟和调度开销：_s $ pi $ _ $ - _ 838_ $ = _365.626_ - _63.586_ - _2L.964_ = *280.076 k *s \*s

This value for the execution time is very interesting. At first, by considering the time expended in the critical section, one could assume that the execution time would be a value close to 100 *K*s, but the execution was shown to take nearly three times that value.

> 执行时间的此值非常有趣。首先，通过考虑关键部分中花费的时间，可以假设执行时间将是接近 100 *k *s 的值，但执行显示该值接近该值的三倍。

By analyzing the trace output, it is possible to see that in addition to the critical section, the execution time was influenced by the timer routines, by the execution of the system call _do_notify_resume()_ that added *74.272 K*s, and by the execution of the function _sys_rt_sigreturn()_ that added more 11.080 *K*s. Moreover, the execution of `mutex_unlock()` added more 73.306 *K*s to the execution time. These operations added 158.658 *K*s to the execution time of the activation of this task.

> 通过分析跟踪输出，可以看到除了临界部分外，执行时间还受计时器例程的影响，通过系统呼叫的执行*do_notify_resume()*添加了 *74.272 k *s，并且受到 *74.272 k *s 的影响。函数的执行* sys_rt_sigreturn()*添加了更多 11.080 *k *s。此外，执行 `mutex_unlock()` 在执行时间中添加了更多 73.306 *k *s。这些操作在激活此任务的执行时间中添加了 158.658 *k *s。

Once these values are defined, it is possible to explain the timing behavior of this task activation drawing the timeline of Figure [9](#_bookmark21).

> 一旦定义了这些值，就可以解释此任务激活的定时行为绘制图[9](#\_ bookmark21)的时间表。

We now continue the trace of the high-priority task.

> 现在，我们继续进行高优先级任务的痕迹。

![](./media/image148.png)
![](./media/image150.png)
![](./media/image151.png)
![](./media/image152.png)
<img src="./media/image160.png" style="width:0.2388in;height:0.14583in" />

Figure 9. Timeline of task pi-838.

> 图 9.任务 PI-838 的时间表。
> ![](./media/image161.png) > ![](./media/image162.png) > ![](./media/image163.png) > ![](./media/image168.png) > ![](./media/image169.png) > ![](./media/image171.png)

Figure 10. <span id="_bookmark22" class="anchor"></span>Timeline of task pi-839.

> 图 10. <span ID =“ \_ bookmark22” class =“锚”> </span>任务 PI-839 的时间表。

The execution time of the system call _read()_ was 191.341 *K*s, which is much greater than 5.609 *K*s, which was its execution time in the absence of blocking, in the previous example.

> 系统呼叫的执行时间*read()*是 191.341 *k *s，大于 5.609 *k *s，这是在上一个示例中没有阻塞的情况下执行时间。

<img src="./media/image177.png" style="width:5.60232in;height:1.91667in" />

After returning to user space, the function that handles the timer signals is executed again. That is because the task ran over its period, and a new signal was delivered in order to start a new task activation.

> 返回用户空间后，再次执行处理计时器信号的功能。这是因为该任务在其周期内运行，并且发出了新的信号以开始新的任务激活。

After handling the signal, the task suspends its execution. It happened because the task was not implemented to deal with a deadline miss. In this case, the use of our trace tool assisted in the discovery of the problem and what factors influenced in this missed deadline.

> 处理信号后，任务暂停其执行。之所以发生，是因为没有执行该任务来处理截止日期的错过。在这种情况下，我们的微量工具的使用有助于发现问题，以及在这个错过的截止日期中影响哪些因素。

After the context switch that completes the task execution at line 108, it is possible to determine the response time _R$pi$_$—_839_$, defined as the time interval between this event and the event that woke the task at line 2. This activation has shown the response time _R$pi$_$—_839_$ of 448.573 *K*s.

> 在第 108 行完成任务执行的上下文开关之后，可以确定响应时间 _r $ pi $ _ $ - _ 839_ $，定义为此事件之间的时间间隔和在第 2 行中唤醒任务的事件之间的时间间隔。此激活显示了响应时间*r $ pi $ * $ - _ 839_ $ 448.573 *k *s。

The exit-scheduling overhead is the time interval between the call of _schedule()_ and the context switch to state _S_ at lines 107 and 108, respectively. It was 15.449 *K*s. This overhead, when added to the entry-scheduling overhead, gives a total of 21.517 *K*s of scheduler overhead.

> 出口安排开销是 *schedule()*的呼叫和上下文切换到第 107 和 108 行的状态* s*之间的时间间隔。是 15.449 *k *s。当添加到入口安排开销中时，该开销总共给出了 21.517 *k *s 的调度程序开销。

The busy window of this activation is the time interval between the start and the end of the task execution, indicated by the context switch at line 16 and the context switch at line 108. It resulted in a _W$pi$_$—_839_$ of 383.999 *K*s.

> 此激活的繁忙窗口是任务执行的开始和结束之间的时间间隔，该执行的开始和结束，由第 16 行的上下文开关和第 108 行的上下文开关表示。它导致*W $ pi $ * $ _ $ - _ 839\_ $383.999 *k *s。

Considering the already-computed _B$pi$_$—_839_$ and the absence of interference, it is possible to estimate the execution time as the response time, minus the blocking, release jitter and scheduler overhead, which results in _S$pi$_$—_839_$ = _448.573_ — _64.574_ — _l78.545_ — _2l.5l7_ = *l83.937 K*s.

> 考虑到已经计算的 _b $ pi $ _ $ - _ 839_ $和缺乏干扰，可以将执行时间估算为响应时间，减去阻塞，释放抖动和调度程序开销，这导致 *s $ pi $* $ - _ 839_ $ = _448.573_ - _64.574_ - _l78.545_ - _2l.5l7_ = *l83.937 k *s。

Once these values are defined, it is possible to draw the activation timeline, shown in Figure [10](#_bookmark22).

> 一旦定义了这些值，就可以绘制激活时间表，如图[10](#\_ bookmark22)如图所示。

By looking at the timeline, we obtain the reason for the deadline miss that is now clear. The blocking time added to the task _pi_ — _838_. We can conclude that the initial setup defined in Table [II](#_bookmark20) is unfeasible.

> 通过查看时间表，我们获得了现在明确的截止日期的原因。添加到任务 _PI\_\_ - \_838_ 的阻塞时间。我们可以得出结论，表[ii](#\_ bookmark20)中定义的初始设置是不可行的。

# 7. RESULTS FROM THE CASE STUDY

> ＃7。案例研究的结果

By applying the rules for the interpretation of the trace and the determination of the values of the several timing properties, we performed a complete analysis of a section of the trace.

> 通过应用规则来解释迹线和确定几个时序属性的值，我们对轨迹的一节进行了完整的分析。

![](./media/image178.png)
<img src="./media/image182.png" style="width:0.51524in" />

Figure 11. <span id="_bookmark24" class="anchor"></span>Response time.

> 图 11. <span ID =“ \_ bookmark24” class =“锚”> </span>响应时间。

In order to facilitate the analysis, we have chosen the trace that uses _raw spinlocks_ for mutual exclusion. The analysis was performed only for the highest-priority task, which does not suffer interference from other processes, only from interrupts. The data gathering was carried out by using a shell script that filtered the data and calculated the times in nanoseconds. An example of the output of our script is shown as follows:

> 为了促进分析，我们选择了使用 _raw Spinlocks_ 进行相互排斥的迹线。该分析仅是针对最高优先级任务的，该任务不会受到其他过程的干扰。数据收集是通过使用过滤数据并在纳秒中计算时间的外壳脚本进行的。脚本输出的一个示例如下：

![](./media/image183.png)

From a trace of 2 s we discarded the first 600 ms to remove the interference from the scripts controlling the experiment. From this new trace, we evaluated the 5259 task arrivals. The output of this script was used to generate the charts discussed in the following subsections.

> 从 2 s 的痕迹中，我们丢弃了前 600 毫秒，以从控制实验的脚本中删除干扰。从这个新的痕迹中，我们评估了 5259 个任务到达。该脚本的输出用于生成以下小节中讨论的图表。

## 7.1 _Response time_

> ## 7.1 _Response Time _

The chart of Figure [11](#_bookmark24) shows the response time of task activations.

> 图[11](#\_ bookmark24)的图表显示了任务激活的响应时间。

Regarding response times, the shortest response time was observed when the task was neither blocked nor preempted. In this case, its response time is the sum of the release jitter, the entryscheduling overhead, its execution time, and the exit-scheduling overhead. The greatest response time was 620.147 *K*s, and it has the following characteristics:

> 关于响应时间，当任务既没有被阻止也没有抢占时观察到最短的响应时间。在这种情况下，其响应时间是发布抖动的总和，入门仪的开销，执行时间和出口安排开销的总和。最大的响应时间是 620.147 *k *s，它具有以下特征：

![](./media/image185.png)

The cause of the high response time was blocking. By analyzing the trace for this activation, we have seen that the task was blocked four times in three mutual exclusion variables during its execution. Two of these variables were RT Mutex: at _sighand-&gt;siglock_, the task was blocked twice for 94.421 and 94.243 *K*s and at _new_timer-&gt;it_lock_ by 94.385 *K*s, and one variable was a raw spinlock, associated with the read function of the module, which blocked the task for 101.908 *K*s.

> 高响应时间的原因是阻塞。通过分析此激活的迹线，我们已经看到该任务在执行过程中在三个相互排除变量中被阻止了四次。与模块的读取功能相关联，该功能阻止了 101.908 *k *s 的任务。

The task was blocked long enough for two more activations of the timer, so the execution time of the task was also penalized, because of the execution of a second signal handler.

> 该任务被阻止了足够长的时间，以便对计时器进行另外两个激活，因此由于执行第二个信号处理程序，任务的执行时间也受到了惩罚。

## 7.2 _Release jitter_

> ## 7.2 _release 抖动_

Figure [12](#_bookmark26) shows the release jitter:

> 图[12](#\_ bookmark26)显示了发行抖动：

The release jitter stays below 50 *K*s most of the time, with peaks of 31, 32, and 33 *K*s. This pattern is caused by the fact that, as there are only two tasks beyond those responsible for system housekeeping, most activations are directed to idle processors. Only in three cases the task arrives at a processor that is really executing some tasks.

> 发行抖动大部分时间都保持在 50 *k *s 以下，峰值为 31、32 和 33 *k *s。这种模式是由于以下事实引起的：由于除了负责系统家务的那些任务之外，大多数激活都针对闲置处理器。只有在三种情况下，任务才能到达真正执行某些任务的处理器。

![](./media/image187.png)
<img src="./media/image188.png" style="width:0.51524in" />

Figure 12. <span id="_bookmark26" class="anchor"></span>Release jitter.

> 图 12. <span ID =“ \_ bookmark26” class =“锚”> </span>释放抖动。
> ![](./media/image189.png) > <img src="./media/image193.png" style="width:0.51518in" />

Figure 13. <span id="_bookmark27" class="anchor"></span>Scheduling execution time.

> 图 13. <span ID =“ \_ bookmark27” class =“锚”> </span>调度执行时间。

## 7.3 _Scheduling_

> ## 7.3 _scheduling_

The execution time of the routines of entry-scheduling overhead and exit-scheduling overhead is shown in Figure [13](#_bookmark27).

> 在图[13](#\_ bookmark27)中显示了进入安排开销和出口开发开销的例程的执行时间。

Regarding the entry-scheduling overhead, only in two executions it took more than 10 *K*s to complete. All other executions last less than 8 *K*s each one. Although these two longer executions seem to be strange at first, by examining the full traces, it is possible to explain what happened regarding the execution flow, which were indeed different in these two runs.

> 关于入口安排开销，只有在两次执行中，才完成了 10 *k *s 的完成。所有其他执行均持续少于 8 *k *s。尽管这两个较长的执行起初似乎很奇怪，但通过检查完整的痕迹，可以解释有关执行流的情况，这在这两个运行中确实有所不同。

During the exit-scheduling overhead, we can see a good example of the difference between _realtime_ and _real-fast_. Despite the execution time of the exit-scheduling overhead, in most cases, being greater than the execution time of the entry-scheduling overhead, the worst execution time of the exit-scheduling overhead is smaller than the worst execution time of the entry-scheduling overhead, for these activations.

> 在出口安排开销期间，我们可以看到一个很好的例子 _realtime_ 和 _real-fast_ 之间的差异。尽管执行出口安排开销的时间，但在大多数情况下，要大于入口安排开销的执行时间，但出口安排的上空开销中最差的执行时间小于入口划分的最差的执行时间开销，用于这些激活。

## 7.4 _Blocking_

> ## 7.4 _ blocking_

Figure [14](#_bookmark28) shows the sum of blocking time of each activation of _pi_ task.

> 图[14](#* bookmark28)显示了\_pi*任务的每个激活的阻止时间的总和。

Most blocking scenarios lasted about *l00 K*s. Many of these times are the times of blocking caused by the shared lock within the read function of the module. However, because the two threads _pi_ also access at the same time functions of the system, they end up sharing other locks, as in the blocking example showed in Section [7.1](#_bookmark25).

> 大多数阻塞场景持续了大约 *l00 k *s。其中许多时间是由模块的读取函数中共享锁定引起的阻止时代。但是，由于两个线程* pi*也同时访问了系统的功能，因此它们最终共享其他锁，如[7.1]节所示的阻止示例(#\_ bookmark25)中所示。

Interestingly, locks _sighand-&gt;siglock_ and _new_timer-&gt;it_lock_, which are RT spinlocks, cause a contention of about 90 *K*s, which gives the graph its characteristic of showing various events between 0 and just over 100 *K*s, where we find the blocking from the shared locking in the module and one blocking of one of these locks. When there are two blockings, the measurements are close to 180 *K*s. When there are three blockings, they are close to 260 *K*s and close to 340 *K*s with four blockings. This feature is so mainly because the two tasks eventually synchronize because of their competition for the same mutual exclusion variables and exhibit the same behavior suffering more blockings.

> 有趣的是，锁 _sighand-＆gt; siglock_ 和 _new_timer-＆gt; it_lock_ 是 rt spinlocks，导致大约 90 *k *s 的争论，该图的特征在于显示 0 *k *k *之间的各种事件的特征 S，在其中找到来自模块中共享锁定的阻塞，并在其中一个锁中封锁。当有两个阻塞时，测量值接近 180 *k *s。当有三个障碍物时，它们接近 260 *k *s，接近 340 *k \*s，带有四个阻塞。此功能之所以如此，主要是因为这两个任务最终是因为他们争夺相同的相互排斥变量并表现出相同的行为遭受更多阻挡。

![](./media/image194.png)
<img src="./media/image197.png" style="width:0.50514in" />

Figure 14. <span id="_bookmark28" class="anchor"></span>Blocking.

> 图 14. <span ID =“ \_ bookmark28” class =“锚”> </span>阻止。
> ![](./media/image198.png) > <img src="./media/image199.png" style="width:0.51517in" />

Figure 15. <span id="_bookmark29" class="anchor"></span>Interference.

> 图 15. <span ID =“ \_ bookmark29” class =“锚”> </span>干涉。

## 7.5 _Interference_

> ## 7.5 _ interference _

Figure [15](#_bookmark29) shows the busy period of interrupts that caused interference on the high-priority task.

> 图[15](#\_ bookmark29)显示了导致干扰高优先级任务的繁忙期间。

There were a total of 1080 interrupts. Only one was not from the timer but an NMI, in which handler lasted for 8 *K*s. Despite the execution time peaks at 38 and 25 *K*s, the duration of the execution window of the timer interrupts tends to be larger for a reason: they occur simultaneously in different processors, causing blocking. For example, the trace in the following is from the time when the interrupt that caused the greatest interference was activated:

> 总共有 1080 个中断。只有一个不是计时器，而是 NMI，其中处理程序持续了 8 *k *s。尽管执行时间达到 38 和 25 *k *s 的峰值，但计时器中断的执行窗口的持续时间往往更大，原因是它们同时发生在不同的处理器中，导致阻塞。例如，以下轨迹是从引起最大干扰的中断的时间开始：

![](./media/image200.png)

In this example, four interrupts occurred simultaneously in four different processors, which competed for access to the same critical sections. In this case, the handler that interrupted the highest-priority task waited for *44.253 K*s for the _raw_spinlock() xtime_lock()_.

> 在此示例中，在四个不同的处理器中同时发生了四个中断，这些处理器竞争了访问相同关键部分的竞争。在这种情况下，打断最高优先级任务的处理程序等待 *44.253 k *s for _raw_spinlock()xtime_lock()_。

## 7.6 _Execution time_

> ## 7.6 _Execution Time _

Finally, Figure [16](#_bookmark30) shows the execution time of each activation. The lowest execution time was 64 *K*s. Most execution times, 79.72 % (4193 of 5259), were in the range of *93*I *98 K*s. The difference between these times and the lowest is because, in most cases, the function _do_notify_resume()_ performs maintenance time functions for the kernel, which sometimes does not happen, as when we have the lowest execution time.

> 最后，图[16](#_ bookmark30)显示了每个激活的执行时间。最低的执行时间是 64 *k *s。大多数执行时间为 79.72％(5259 中的 4193)，范围为 *93 *i *98 k *s。这些时间和最低的区别是因为在大多数情况下，函数\_do_notify_resume()_ \_执行内核的维护时间函数，有时不会发生，就像我们拥有最低的执行时间一样。

![](./media/image203.png)
<img src="./media/image205.png" style="width:0.51021in" />

Figure 16. <span id="_bookmark30" class="anchor"></span>Execution time.

> 图 16. <span ID =“ \_ bookmark30” class =“锚”> </span>执行时间。

The longest execution times, over 110 *K*s, are caused when, because of blocking, interference, or delay, the system misses the deadline and has to handle the signals that would wake up the next activation before suspension.

> 最长的执行时间，超过 110 *k *s 是由于阻塞，干扰或延迟而导致的，系统会错过截止日期，并且必须处理在悬架之前唤醒下一次激活的信号。

# 8. CONCLUSION

> ＃8。结论

There is great interest from both developers and researchers in transforming Linux in a realtime operating system. But cooperation is limited by the fact that these two communities use different abstractions to model system components and different methods of system validation. Task models used in the scheduling theory are usually too simple. They do not capture the constraints and task dependencies that appear when real-time applications run on a Linux kernel. Despite the vast literature on real-time scheduling, few of these results are to be used by the Linux development community.

> 开发人员和研究人员对实时操作系统中的 Linux 都有极大的兴趣。但是，合作受到这两个社区使用不同的抽象来建模系统组件和系统验证方法的不同方法的事实的限制。调度理论中使用的任务模型通常太简单了。他们不会捕获实时应用程序在 Linux 内核上运行时出现的约束和任务依赖性。尽管有关于实时时间表的大量文献，但 Linux 开发界很少使用这些结果。

Although the main objective of the PREEMPT RT patch is to reduce system latency, it also simplifies the control flow inside the Linux kernel, which makes it more amenable to modeling. Priority inversion is mostly avoided by reducing the code sections where the system remains with interrupts and preemption disabled. Notwithstanding, the actual behavior of the PREEMPT RT Linux is far from the simple models used in the real-time scheduling theory.

> 尽管抢先 RT 补丁的主要目标是减少系统延迟，但它也简化了 Linux 内核内部的控制流，这使其更适合建模。优先倒置主要通过减少系统中断和预先抢先的代码部分来避免优先倒置。尽管如此，抢占 RT Linux 的实际行为远非实时调度理论中使用的简单模型。

In this paper, we make three contributions in the direction of applying the real-time scheduling theory to real systems based on the PREEMPT RT Linux:

> 在本文中，我们在将实时调度理论应用于基于抢先 RT Linux 的真实系统的方向上做出了三项贡献：

- PREEMPT RT Linux kernel mechanisms that impact the timing of real-time tasks were identified and mapped to abstractions used by the real-time scheduling theory;

> - 鉴定并映射到影响实时任务时间安排时间的 RT Linux 内核机制，并映射到实时调度理论所使用的抽象；

- A customized trace tool was created, such that it allows the measurement of the delays associated with the main abstractions of the real-time scheduling theory;

> - 创建了一个定制的跟踪工具，以便允许测量与实时调度理论的主要抽象相关的延迟；

- This customized trace tool was used to characterize the timelines of the PREEMPT RT Linux kernel.

> - 该自定义的跟踪工具用于表征 Preempt RT Linux 内核的时间表。

The mapping between Linux kernel and real-time abstractions, facilitated by the response-time analysis, creates a new point of view over the Linux execution. This mapping was possible because of the modifications of the Linux kernel; many of them are part of the PREEMPT RT patch or were implemented first on PREEMPT RT and then ported to the mainstream kernel. This was the case with the fully preemptible mode and the handling of IRQs by kernel threads.

> 响应时间分析促进的 Linux 内核和实时抽象之间的映射为 Linux 执行创造了新的观点。由于 Linux 内核的修改，因此可能进行了映射。其中许多是抢先 RT 补丁的一部分，或者首先在抢占 RT 上实施，然后移植到主流内核。完全可预先抢占的模式和内核线程对 IRQ 的处理就是这种情况。

Nevertheless, only the mapping would not be enough to observe the kernel execution from this new point of view. Ftrace proved its power and usability in the creation of a new view format, mainly using the already-implemented methods. The timing characterization of the Linux kernel was then possible as a consequence of the abstraction mapping and the new trace tool.

> 然而，只有映射不足以从这个新角度观察内核执行。Ftrace 证明了其在创建新视图格式的功能和可用性，主要使用已经实现的方法。因此，由于抽象映射和新的痕量工具，可以实现 Linux 内核的定时表征。

The main contribution of this paper is the description of the Linux kernel timeline based on realtime scheduling abstractions. The development and evaluation of new algorithms, both to kernel and user space, can be made using these abstractions. We believe this characterization is an important step in the direction of creating correct task models of the PREEMPT RT Linux and developing analytical methods for its schedulability analysis. It will also help in the sharing of information, making new implementations easy to understand by the researchers, and the advantages of new algorithms implemented by researchers being clearly understood by practitioners.

> 本文的主要贡献是基于实时计划抽象的 Linux 内核时间表的描述。可以使用这些抽象进行新算法的开发和评估，包括内核和用户空间。我们认为，这种表征是在创建 Preement RT Linux 的正确任务模型并为其计划分析开发分析方法的方向上的重要一步。这也将有助于共享信息，使研究人员易于理解新的实施，以及研究人员实施的新算法的优势，从业人员清楚地理解了研究人员。

As future work, the automation of the trace analysis will help on the evaluation of new algorithms. Furthermore, as the trace tool generates a huge amount of data, the ability to make this evaluation on the fly by a long period is another challenge. An interesting challenge would be the evaluation of the deadline scheduler [4](#_bookmark35) that uses a different method to choose the priority of tasks, in such way that the higher-priority task depends on the deadline of the task and not on a fixed priority.

> 作为未来的工作，痕量分析的自动化将有助于评估新算法。此外，由于痕量工具会生成大量数据，因此长期进行该评估的能力是另一个挑战。一个有趣的挑战将是对截止日期调度程序的评估[4](#\_ bookmark35)，它使用不同的方法选择任务的优先级，以至于更高优先级的任务取决于任务的截止日期，而不是在固定优先级。

# REFERENCES

1. <span id="_bookmark32" class="anchor"></span>Red Hat, Inc. Red Hat Enterprise MRG. Available at: [http://www.redhat.com/f/pdf/MRG_Datasheet.pdf](http://www.redhat.com/f/pdf/MRG_Datasheet.pdf) last accessed 17 September 2014.
2. <span id="_bookmark33" class="anchor"></span>MontaVista. Real-time. Available at: [http://www.mvista.com/solution-real-time.html](http://www.mvista.com/solution-real-time.html) > last accessed 17 September 2014.
3. <span id="_bookmark34" class="anchor"></span>imus$RT$ : Linux testbed for multiprocessor scheduling in real-time systems. Available at: [http://www.litmus-rt.org/](http://www.litmus-rt.org/) last accessed 17 September 2014.
4. <span id="_bookmark35" class="anchor"></span>Lelli J, Lipari G, Faggioli D, Cucinotta T. An efficient and scalable implementation of global EDF in Linux. _Proceedings of the 7th Annual Workshop on Operating Systems Platforms for Embedded Real-Time applications (OSPERT 2011)_, Porto, Portugal, 2011; 6–15.
5. <span id="_bookmark36" class="anchor"></span>Real-time Linux wiki. Available at: [https://rt.wiki.kernel.org/](https://rt.wiki.kernel.org/) last accessed 17 September 2014.
6. <span id="_bookmark37" class="anchor"></span>Corbet J. Linux at NASDAQ OMX*. Linux Weekly News*, October 2010. Available at: [http://lwn.net/Articles/411064/](http://lwn.net/Articles/411064/) last accessed 17 September 2014.
7. <span id="_bookmark38" class="anchor"></span>Bastoni A., Brandenburg B, Anderson J. An empirical comparison of global, partitioned, and clustered multiprocessor EDF schedulers. _2010 IEEE 31st Real-Time Systems Symposium (RTSS)_, San Diego, California, 2010; 14–24. DOI: 10.1109/RTSS.2010.23.
8. <span id="_bookmark39" class="anchor"></span>Lelli J, Faggioli D, Cucinotta T, Lipari G. An experimental comparison of different real-time schedulers on multicore systems. _Journal of Systems and Software_ 2012; **85**(10):2405–2416.
9. <span id="_bookmark40" class="anchor"></span>Gleixner T. Realtime Linux: academia v. reality. _Linux Weekly News_ July 2010. Available at: [http://lwn.net/Articles/](http://lwn.net/Articles/471973/) > [471973/](http://lwn.net/Articles/471973/) last accessed 17 September 2014.
10. <span id="_bookmark41" class="anchor"></span>Brandenbug B, Anderson J. Joint opportunities for real-time Linux and real-time system research. _Proceedings of the 11th Real-Time Linux Workshop (RTLWS 2009)_, Dresden, Germany, 2009; 19–30.
11. <span id="_bookmark42" class="anchor"></span>Hart DV, Rostedt S. Internals of the RT patch. _Ottawa Linux Symposium_, Ottawa, Ontario, 2007; 161–172.
12. <span id="_bookmark43" class="anchor"></span>Buttazzo G. _Hard Real-time Computing Systems: Predictable Scheduling Algorithms and Applications_ (2nd edn). Springer: Santa Clara, California, 2005.
13. <span id="_bookmark44" class="anchor"></span>Davis RI, Burns A. A survey of hard real-time scheduling for multiprocessor systems. _ACM Computing Surveys_ October 2011; **43**(4):35:1–35:44. DOI: 10.1145/1978802.1978814.
14. <span id="_bookmark45" class="anchor"></span>Joseph M, Pandya PK. Finding response times in a real-time system. _Computer Journal_ 1986; **29**(5):390–395.
15. <span id="_bookmark46" class="anchor"></span>Corbet J, Rubini A, Kroah-Hartman G. _Linux Device Driver_ (3rd edn). O’Reilly Media: Sebastopol, California, 2005.
16. <span id="_bookmark47" class="anchor"></span>Love R. _Linux Kernel Development_ (3rd edn). Addison-Wesley: Crawfordsville, Indiana, 2010.
17. <span id="_bookmark48" class="anchor"></span>Rostedt S. RT-mutex subsystem with PI support. Available at: [https://www.kernel.org/doc/Documentation/](https://www.kernel.org/doc/Documentation/rt-mutex-design.txt) [rt-mutex-design.txt](https://www.kernel.org/doc/Documentation/rt-mutex-design.txt) last accessed 17 September 2014.
18. <span id="_bookmark49" class="anchor"></span>Guniguntala D, McKenney PE, Triplett J, Walpole J. The read-copy-update mechanism for supporting real-time applications on shared-memory multiprocessor systems with Linux. _IBM Systems Journal_ 2008; **47**(2):221–236.
19. <span id="_bookmark50" class="anchor"></span>McKenney P. What is RCU, fundamentally? _Linux Weekly News_, December 2007. Available at: [http://lwn.net/](http://lwn.net/Articles/262464/) [Articles/262464/](http://lwn.net/Articles/262464/) last accessed 17 September 2014.
20. <span id="_bookmark51" class="anchor"></span>McKenney P. What is RCU? Part 2: Usage. _Linux Weekly News_ December 2007. Available at: [http://lwn.net/Articles/](http://lwn.net/Articles/263130/) [263130/](http://lwn.net/Articles/263130/) last accessed 17 September 2014.
21. <span id="_bookmark52" class="anchor"></span>McKenney P. The RCU API, 2014 Edition _Linux Weekly News_ September 2014. Available at: [http://lwn.net/Articles/](http://lwn.net/Articles/609904/) [609904/](http://lwn.net/Articles/609904/) last accessed 11 April 2015.
22. <span id="_bookmark53" class="anchor"></span>Brandenburg B, Leontyev H, Anderson J. Accounting for interrupts in multiprocessor real-time systems. _15th IEEE International Conference on Embedded and Real-Time Computing Systems and Applications, 2009. RTCSA ’09_, Beijing, China, August 2009; 273–283. DOI: 10.1109/RTCSA.2009.37.
23. <span id="_bookmark54" class="anchor"></span>Kenna C, Herman J, Brandenburg B, Mills A, Anderson J. Soft real-time on multiprocessors: are analysis-based schedulers really worth it? _Real-Time Systems Symposium (RTSS), 2011 IEEE 32nd_, Vienna, Austria, 2011; 93–103. DOI: 10.1109/RTSS.2011.16.
24. <span id="_bookmark55" class="anchor"></span>Brandenburg B. A fully preemptive multiprocessor semaphore protocol for latency-sensitive real-time applications. _2013 25th Euromicro Conference on Real-Time Systems (ECRTS)_, Paris, France, 2013; 292–302. DOI: 10.1109/ECRTS.2013.38.
25. Bastoni A, Brandenburg B, Anderson J. Is semi-partitioned scheduling practical? _2011 23rd Euromicro Conference on Real-Time Systems (ECRTS)_, Porto, Portugal, 2011; 125–135. DOI: 10.1109/ECRTS.2011.20.
26. <span id="_bookmark56" class="anchor"></span>Spear A, Levy M, Desnoyers M. Using tracing to solve the multicore system debug problem. _Computer_ 2012; **45**(12):60–64.
27. <span id="_bookmark57" class="anchor"></span>Toupin D. Using tracing to diagnose or monitor systems. _Software, IEEE_ 2011; **28**(1):87–91.
28. <span id="_bookmark58" class="anchor"></span>Brandenburg B, Anderson J. Feather-trace: a light-weight event tracing toolkit. _Proceedings of the Third International Workshop on Operating Systems Platforms for Embedded Real-Time Applications (OSPERT)_, Pisa, Italy, 2007; 19–28.
29. <span id="_bookmark59" class="anchor"></span>Rostedt S. Using the TRACE*EVENT() macro (Part 1)*. Linux Weekly News\_, March 2010. Available at: [http://lwn.](http://lwn.net/Articles/379903/) [net/Articles/379903/](http://lwn.net/Articles/379903/) last accessed 17 September 2014.
30. <span id="_bookmark60" class="anchor"></span>Rostedt Steven. Debugging the kernel using Ftrace—part 1*. Linux Weekly News*, December 2009. Available at: [http://](http://lwn.net/Articles/365835/) [lwn.net/Articles/365835/](http://lwn.net/Articles/365835/) last accessed 17 September 2014.
31. <span id="_bookmark61" class="anchor"></span>Lttng project. Available at: [http://lttng.org/](http://lttng.org/) last accessed 17 September 2014.
32. <span id="_bookmark62" class="anchor"></span>Rostedt S. Secrets of the Ftrace function tracer*. Linux Weekly News*, January 2010. Available at: [http://lwn.net/](http://lwn.net/Articles/370423/) [Articles/370423/](http://lwn.net/Articles/370423/) last accessed 17 September 2014.
33. <span id="_bookmark63" class="anchor"></span>Corbet J. Dynamic probes with ftrace*. Linux Weekly News*, July 2009. Available at: [http://lwn.net/Articles/343766/](http://lwn.net/Articles/343766/) last accessed 17 September 2014.
34. <span id="_bookmark64" class="anchor"></span>Rostedt Steven. The x86 NMI iret problem*. Linux Weekly News*, March 2012. Available at: [http://lwn.net/Articles/](http://lwn.net/Articles/484932/) [484932/](http://lwn.net/Articles/484932/) last accessed 17 September 2014.
35. <span id="_bookmark65" class="anchor"></span>OSADL. OSADL project: realtime Linux. Available at: https://[www.osadl.org/Realtime-Linux.projects-realtime-](http://www.osadl.org/Realtime-Linux.projects-realtime-) linux.0.html last accessed 15 April 2014.
