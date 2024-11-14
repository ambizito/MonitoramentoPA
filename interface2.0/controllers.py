# controllers.py
from services.logins_service import LoginsService
from models.mongodb_model import MongoDBModel
from models.api_model import APIModel
from views.janela_principal import JanelaPrincipal

class Controller:
  def __init__(self):
    self.model = {
      'mongodb': MongoDBModel(),
      'api': APIModel()
      }
    # Outros atributos e inicializações
    executable_path = r"C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug\ProcessoAgil.Logins.exe"
    working_dir = r"C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug"
    self.logins_service = LoginsService(executable_path, working_dir)

  def run(self):
        self.app = JanelaPrincipal(self)
        self.app.mainloop()