import random

class CombatEngine:
    def __init__(self):
        # Tabla maestra completa de los 18 tipos de Pokémon
        # 1.0 = Daño normal, 2.0 = Súper efectivo, 0.5 = Poco efectivo, 0.0 = Inmune
        self.tabla_tipos = {
            "normal": {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
            "fire": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0, "bug": 2.0, "rock": 0.5, "dragon": 0.5, "steel": 2.0},
            "water": {"fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0, "rock": 2.0, "dragon": 0.5},
            "electric": {"water": 2.0, "electric": 0.5, "grass": 0.5, "ground": 0.0, "flying": 2.0, "dragon": 0.5},
            "grass": {"fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5, "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0, "dragon": 0.5, "steel": 0.5},
            "ice": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 0.5, "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 0.5},
            "fighting": {"normal": 2.0, "ice": 2.0, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2.0, "ghost": 0.0, "dark": 2.0, "steel": 2.0, "fairy": 0.5},
            "poison": {"grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0.0, "fairy": 2.0},
            "ground": {"fire": 2.0, "electric": 2.0, "grass": 0.5, "poison": 2.0, "flying": 0.0, "bug": 0.5, "rock": 2.0, "steel": 2.0},
            "flying": {"electric": 0.5, "grass": 2.0, "fighting": 2.0, "bug": 2.0, "rock": 0.5, "steel": 0.5},
            "psychic": {"fighting": 2.0, "poison": 2.0, "psychic": 0.5, "dark": 0.0, "steel": 0.5},
            "bug": {"fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0, "steel": 0.5, "fairy": 0.5},
            "rock": {"fire": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.5, "flying": 2.0, "bug": 2.0, "steel": 0.5},
            "ghost": {"normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5},
            "dragon": {"dragon": 2.0, "steel": 0.5, "fairy": 0.0},
            "dark": {"fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5, "fairy": 0.5},
            "steel": {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0, "rock": 2.0, "steel": 0.5, "fairy": 2.0},
            "fairy": {"fire": 0.5, "fighting": 2.0, "poison": 0.5, "dragon": 2.0, "dark": 2.0, "steel": 0.5}
        }

    def calcular_danio(self, tipo_ataque, tipo_defensor, danio_base):
        t_atk = tipo_ataque.lower().strip()
        t_def = tipo_defensor.lower().strip()
        
        # Si el tipo no existe en la tabla (ej. error de escritura), multiplica por 1.0
        multiplicador = self.tabla_tipos.get(t_atk, {}).get(t_def, 1.0)
        return round(danio_base * multiplicador), multiplicador

    def generar_dummy(self, tipo_base="normal"):
        """El motor lógico ahora permite cualquier tipo y mantiene los rangos estrictos de la pauta"""
        hp = random.randint(80, 150)
        return {
            "name": "Dummy AI",
            "type": tipo_base,
            "hp": hp,
            "attacks": [
                {"name": "Ataque Alfa", "damage": random.randint(15, 45), "type": tipo_base},
                {"name": "Ataque Beta", "damage": random.randint(15, 45), "type": "normal"}
            ]
        }