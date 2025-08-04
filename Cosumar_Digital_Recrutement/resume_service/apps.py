from django.apps import AppConfig
import threading
import os

class ResumeServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'resume_service'

    def ready(self):
        if os.environ.get('RUN_MAIN') and os.environ.get('RUN_MAIN', None) != 'true':
            return
        print(">> ResumeServiceConfig.ready() called")

        def run_in_thread():
            from resume_service.mail import main_loop
            print(">> Starting main_loop in thread...")
            main_loop()

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
