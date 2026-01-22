#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta
from pathlib import Path

# ================== ARCHIVOS ==================
SEMESTRES_PATH = Path("semestres.json")
SALONES_PATH = Path("salones.json")
CURSOS_PATH = Path("cursos.json")
OUT_PATH = Path("reservaciones.json")

# ================== UTILIDADES ==================
DIA_A_WEEKDAY = {
    "lunes": 0,
    "martes": 1,
    "miércoles": 2,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5,
    "sabado": 5,
    "domingo": 6,
}

def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def parse_date(fecha: str):
    return datetime.strptime(fecha, "%Y-%m-%d").date()

def daterange(inicio, fin):
    actual = inicio
    while actual <= fin:
        yield actual
        actual += timedelta(days=1)

def to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)

def traslapa(a_ini, a_fin, b_ini, b_fin) -> bool:
    return a_ini < b_fin and b_ini < a_fin

# ================== GENERADOR ==================
def generar_reservaciones(semestre, cursos, salones):
    fecha_inicio = parse_date(semestre["fecha_inicio"])
    fecha_fin = parse_date(semestre["fecha_fin"])

    # ocupacion[id_salon][fecha] = [(ini, fin)]
    ocupacion = {}

    def disponible(id_salon, fecha, ini, fin):
        ocupacion.setdefault(id_salon, {})
        ocupacion[id_salon].setdefault(fecha, [])
        for x_ini, x_fin in ocupacion[id_salon][fecha]:
            if traslapa(ini, fin, x_ini, x_fin):
                return False
        return True

    def reservar(id_salon, fecha, ini, fin):
        ocupacion[id_salon][fecha].append((ini, fin))

    reservaciones = []
    id_curso = 1

    for curso in cursos:
        for horario in curso["horarios"]:
            dia = horario["dia"].lower()
            if dia not in DIA_A_WEEKDAY:
                raise ValueError(f"Día inválido: {horario['dia']}")

            weekday = DIA_A_WEEKDAY[dia]
            h_ini = to_minutes(horario["hora_inicio"])
            h_fin = to_minutes(horario["hora_fin"])

            fechas = [
                d for d in daterange(fecha_inicio, fecha_fin)
                if d.weekday() == weekday
            ]

            salon_asignado = None

            for salon in salones:
                ok = True
                for f in fechas:
                    iso = f.isoformat()
                    if not disponible(salon["id_salon"], iso, h_ini, h_fin):
                        ok = False
                        break

                if ok:
                    salon_asignado = salon["id_salon"]
                    for f in fechas:
                        iso = f.isoformat()
                        reservar(salon_asignado, iso, h_ini, h_fin)
                        reservaciones.append({
                            "id_curso": id_curso,
                            "id_salon": salon_asignado,
                            "fecha": iso,
                            "hora_inicio": horario["hora_inicio"],
                            "hora_fin": horario["hora_fin"]
                        })
                    break

            if salon_asignado is None:
                raise RuntimeError(
                    f"No hay salón disponible para curso {id_curso} "
                    f"{horario['dia']} {horario['hora_inicio']}-{horario['hora_fin']}"
                )

        id_curso += 1

    return reservaciones

# ================== MAIN ==================
def main():
    semestres_data = load_json(SEMESTRES_PATH)
    salones_data = load_json(SALONES_PATH)
    cursos_data = load_json(CURSOS_PATH)

    semestre = semestres_data["semestres"][0]  # semestre activo
    salones = salones_data["salones"]
    cursos = cursos_data["cursos"]

    reservaciones = generar_reservaciones(semestre, cursos, salones)

    salida = {
        "id_semestre": semestre["id_semestre"],
        "ciclo": semestre["ciclo"],
        "reservaciones": reservaciones
    }

    OUT_PATH.write_text(
        json.dumps(salida, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"✔ Reservaciones generadas: {len(reservaciones)}")
    print(f"📄 Archivo: {OUT_PATH.resolve()}")

if __name__ == "__main__":
    main()
