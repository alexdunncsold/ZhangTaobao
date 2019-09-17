from supervisor import Supervisor

supervisor = Supervisor(dev=True, archive=False)
supervisor.perform_main_loop()
