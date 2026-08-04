# test_minimal.py
from database.config import get_settings
from database.database import init_db, get_session
from services.crud.user import create_user, get_all_users
from models.user import User
from models.ml_task import MLTask
from models.transaction import Transaction
from models.enums import TransactionType, TaskStatus


if __name__ == "__main__":
    settings = get_settings()
    print(settings.APP_NAME)
    print(settings.API_VERSION)
    print(f'Debug: {settings.DEBUG}')
    
    print(settings.DB_HOST)
    print(settings.DB_NAME)
    print(settings.DB_USER)
    
    init_db(drop_all=True)
    print('Init db has been success')
    
    # Создаем тестовых пользователей
    test_user = User(
        username='john_doe',
        email='john@gmail.com',
        password_hash='hashed_password'
    )
    test_user_2 = User(
        username='jane_smith',
        email='jane@gmail.com',
        password_hash='hashed_password'
    )
    test_user_3 = User(
        username='admin_user',
        email='admin@gmail.com',
        password_hash='hashed_password'
    )

    test_task = MLTask(
        user_id=1,  
        input_data={"prompt": "Generate a poem"},
        cost=1
    )
    test_task_2 = MLTask(
        user_id=1,
        input_data={"prompt": "Write a story"},
        cost=1
    )
    
    # Создаем транзакцию
    test_transaction = Transaction(
        user_id=1,
        amount=100,
        transaction_type=TransactionType.DEPOSIT,
        description="Test deposit"
    )
    
    with get_session() as session:
        # Создаем пользователей
        created_user = create_user(test_user, session)
        created_user_2 = create_user(test_user_2, session)
        created_user_3 = create_user(test_user_3, session)
        
        # Добавляем задачи первому пользователю
        test_task.user_id = created_user.id
        test_task_2.user_id = created_user.id
        session.add(test_task)
        session.add(test_task_2)
        
        # Добавляем транзакцию первому пользователю
        test_transaction.user_id = created_user.id
        session.add(test_transaction)
        
        session.commit()
        
        # Получаем всех пользователей
        users = get_all_users(session)
        
    print('-------')
    print(f'Id локального пользователя: {id(test_user)}')
    print(f'Id пользователя из БД: {id(users[0])}')
    print(f'Id одинаковые: {id(test_user) == id(users[0])}')
    
    print('-------')
    print('Пользователи из БД:')        
    for user in users:
        print(user)
        print(f'Баланс пользователя: {user.balance.credits if user.balance else 0} кредитов')
        print('Пользовательские задачи:')
        if len(user.ml_tasks) == 0:
            print('Пользователь не имеет задач')
        else:
            for task in user.ml_tasks:
                print(f'  - Задача ID: {task.id}, Статус: {task.status}, Стоимость: {task.cost}')
        
        print('Транзакции:')
        if len(user.transactions) == 0:
            print('Пользователь не имеет транзакций')
        else:
            for trans in user.transactions:
                print(f'  - Транзакция ID: {trans.id}, Сумма: {trans.amount}, Статус: {trans.status}')