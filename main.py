from supervisor import Supervisor

supervisor = Supervisor('ztb', dev=True, archive=False)
supervisor.perform_main_loop()
