#!/bin/bash

# Couleurs pour un affichage plus clair
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # Pas de couleur

echo -e "${YELLOW}Vérification de la présence de Python 3...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 n'est pas installé ! Veuillez l'installer avant d'exécuter ce script.${NC}"
    exit 1
else
    echo -e "${GREEN}Python 3 est installé.${NC}"
fi

echo -e "${YELLOW}Vérification de la présence de pip...${NC}"
if ! command -v pip &> /dev/null; then
    echo -e "${YELLOW}pip n'est pas détecté. Installation en cours...${NC}"
    python3 -m ensurepip --default-pip
    if ! command -v pip &> /dev/null; then
        echo -e "${RED}L'installation de pip a échoué.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}pip est déjà installé.${NC}"
fi

echo -e "${YELLOW}Mise à jour de pip...${NC}"
pip install --upgrade pip
if [ $? -eq 0 ]; then
    echo -e "${GREEN}pip a été mis à jour avec succès.${NC}"
else
    echo -e "${RED}Échec de la mise à jour de pip.${NC}"
    exit 1
fi

echo -e "${YELLOW}Installation du module requests...${NC}"
pip install requests
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Le module requests a été installé avec succès.${NC}"
else
    echo -e "${RED}Échec de l'installation du module requests.${NC}"
    exit 1
fi

echo -e "${GREEN}Toutes les opérations ont été effectuées avec succès !${NC}"

echo -e "${YELLOW}Installation du module qbittorrent-api...${NC}"
pip install qbittorrent-api
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Le module qbittorrent-api a été installé avec succès.${NC}"
else
    echo -e "${RED}Échec de l'installation du module qbittorrent-api.${NC}"
    exit 1
fi

echo -e "${GREEN}Toutes les opérations ont été effectuées avec succès !${NC}"

echo -e "${YELLOW}Installation du module arrapi...${NC}"
pip install arrapi
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Le module arrapi a été installé avec succès.${NC}"
else
    echo -e "${RED}Échec de l'installation du module arrapi.${NC}"
    exit 1
fi

echo -e "${GREEN}Toutes les opérations ont été effectuées avec succès !${NC}"
