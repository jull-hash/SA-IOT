CREATE DATABASE ZOOFEEDER;
USE ZOOFEEDER;

-- Criação da tabela de Funcionários
CREATE TABLE Funcionario (
    id_funcionario INT PRIMARY KEY AUTO_INCREMENT,
    rfid VARCHAR(255) NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL,
    cargo VARCHAR(50) NOT NULL,
    usuario VARCHAR(100) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL
);

-- Criação da tabela de Recintos (Baias)
CREATE TABLE Recinto (
    id_recinto INT PRIMARY KEY AUTO_INCREMENT,
    nome_identificacao VARCHAR(100) NOT NULL,
    status_trava ENUM('0', '1') DEFAULT '1' -- '0': Aberta, '1': Fechada
);

-- Criação da tabela de Animais
CREATE TABLE Animais (
    id_animais INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    especie VARCHAR(100) NOT NULL,
    cod_tag VARCHAR(255) NOT NULL UNIQUE,
    id_recinto INT,
    FOREIGN KEY (id_recinto) REFERENCES Recinto(id_recinto)
);

-- Histórico de Alimentação (RF002)
CREATE TABLE Historico_alimentacao (
    id_alimentacao INT PRIMARY KEY AUTO_INCREMENT,
    id_animais INT NOT NULL,
    id_funcionario INT NOT NULL,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_animais) REFERENCES Animais(id_animais),
    FOREIGN KEY (id_funcionario) REFERENCES Funcionario(id_funcionario)
);

-- Registro de Entrada/Saída de funcionários E animais nas Baias (RF001)
-- Cada linha tem id_funcionario OU id_animais preenchido (o outro fica NULL)
CREATE TABLE Movimentacoes_baia (
    id_movimentacao INT PRIMARY KEY AUTO_INCREMENT,
    id_recinto INT NOT NULL,
    id_funcionario INT NULL,
    id_animais INT NULL,
    tipo_mov ENUM('Entrada', 'Saida') NOT NULL,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_recinto) REFERENCES Recinto(id_recinto),
    FOREIGN KEY (id_funcionario) REFERENCES Funcionario(id_funcionario),
    FOREIGN KEY (id_animais) REFERENCES Animais(id_animais)
);

-- Tags lidas pelo leitor que ainda não foram cadastradas (painel do admin)
CREATE TABLE Tag_lida (
    uid VARCHAR(255) PRIMARY KEY,
    ultima_leitura DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Login do painel do administrador
CREATE TABLE Administrador (
    id_admin INT PRIMARY KEY AUTO_INCREMENT,
    usuario VARCHAR(100) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL
);

-- Baias iniciais
INSERT INTO Recinto (nome_identificacao) VALUES ('Baia 1'), ('Baia 2');