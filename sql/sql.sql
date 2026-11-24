CREATE TABLE Funcionário 
( 
 ID_funcionario INT PRIMARY KEY auto_increment,  
 RFID varchar(255) not null,  
 Usuário varchar(100) not null,  
 senha varchar(255) not null
); 


CREATE TABLE Recinto 
( 
 ID_Recinto INT PRIMARY KEY auto_increment,  
 Nome_identificacao varchar(100) not null,  
 Status_trava enum('0','1') default '1'
); 


CREATE TABLE Animais 
( 
 ID_animais INT PRIMARY KEY auto_increment,  
 idRecinto INT,  
 cod_tag varchar(255) not null  
); 


CREATE TABLE Historico_alimentacao 
( 
 ID_alimentacao INT PRIMARY KEY auto_increment,  
 idAnimais INT,
 idfuncionario INT,
 data_hora datetime 
); 


CREATE TABLE Movimentacoes_baia 
( 
 ID_movimentacao INT PRIMARY KEY auto_increment,  
 idRecinto INT,  
 idFuncionário INT,
 Tipo_mov enum ('0','1') default '1',  
 Data_hora datetime  
); 


ALTER TABLE Animais ADD FOREIGN KEY(idRecinto) REFERENCES Recinto (ID_Recinto);
ALTER TABLE Historico_alimentacao ADD FOREIGN KEY(idAnimais) REFERENCES Animais (ID_animais);
ALTER TABLE Historico_alimentacao ADD FOREIGN KEY(idFuncionário) REFERENCES Animais (ID_funcionario);
ALTER TABLE Movimentacoes_baia ADD FOREIGN KEY(idRecinto) REFERENCES Recinto (ID_Recinto);
ALTER TABLE Movimentacoes_baia ADD FOREIGN KEY(idFuncionário) REFERENCES Funcionário (ID_funcionario);