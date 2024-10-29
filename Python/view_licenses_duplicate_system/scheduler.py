from database_manager import DatabaseManager

def run_scheduled_task():
    db_manager = DatabaseManager()
    old_data = db_manager.get_previous_results()  # Obtém os dados anteriores
    new_data = db_manager.execute_query()  # Executa a nova consulta
    
    # Armazena novos dados
    if new_data:
        db_manager.store_query_results(new_data)
        new_entries = db_manager.get_new_entries(old_data, new_data)
        
        if new_entries:
            print(f"Novos dados encontrados: {new_entries}")
        else:
            print("Nenhum novo dado encontrado.")
    else:
        print("Nenhum dado encontrado na nova consulta.")

if __name__ == '__main__':
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BlockingScheduler()

    # Executa a cada 2 horas entre 08:00 e 18:00 de segunda a sexta-feira
    scheduler.add_job(run_scheduled_task, CronTrigger(hour='8-18/2', day_of_week='mon-fri'))

    scheduler.start()
