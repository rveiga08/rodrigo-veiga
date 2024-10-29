import win32serviceutil
import win32service
import win32event
import servicemanager
import logging
import os
from scheduler import run_scheduled_task

class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MyQueryService"
    _svc_display_name_ = "Query Service"
    _svc_description_ = "Serviço que realiza consultas periódicas ao banco de dados."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        
        # Configura o log para o serviço
        self.setup_logging()

    def setup_logging(self):
        log_directory = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_directory, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(log_directory, 'service.log'),
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.debug('Service is initializing...')

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        logging.debug('Service is stopping...')

    def SvcDoRun(self):
        logging.debug('Service is starting...')
        try:
            run_scheduled_task()
            logging.debug('Scheduled task started successfully.')
        except Exception as e:
            logging.error(f"Error in service: {e}")
            self.SvcStop()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(MyService)
