# def create_db_and_tables():
#     print("Criando tabelas no banco de dados...")
#     SQLModel.metadata.drop_all(engine)
#     print(SQLModel.metadata.tables.keys())
#     SQLModel.metadata.create_all(engine) 
#     print("Tabelas criadas com sucesso!")

#     with Session(engine) as session:
#         session.commit()

# create_db_and_tables()