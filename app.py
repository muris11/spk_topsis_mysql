from flask import Flask, render_template
import pandas as pd
import numpy as np
import mysql.connector

import os
import sys
import traceback

app = Flask(__name__)


def _log(msg):
    try:
        path = os.path.join(os.path.dirname(__file__), 'spk_debug.log')
        with open(path, 'a', encoding='utf-8') as f:
            f.write(msg + "\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
    except Exception:
        pass

def get_connection():
    _log('get_connection: start')
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="spk_topsis",
            connection_timeout=10,
            use_pure=True
        )
        _log('get_connection: done')
        return conn
    except Exception:
        _log('get_connection: exception')
        with open(os.path.join(os.path.dirname(__file__), 'spk_debug.log'), 'a', encoding='utf-8') as f:
            traceback.print_exc(file=f)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        raise

def get_alternatif():
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT id, kode, nama FROM alternatif ORDER BY id"
    cur.execute(query)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    df = pd.DataFrame(rows, columns=cols)
    cur.close()
    conn.close()
    return df

def get_kriteria():
    _log('get_kriteria: start')
    try:
        conn = get_connection()
        _log('get_kriteria: got connection')
        cur = conn.cursor()
        query = "SELECT id, kode, nama, tipe, bobot_awal FROM kriteria ORDER BY id"
        _log('get_kriteria: executing query')
        cur.execute(query)
        _log('get_kriteria: fetched rows')
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        _log(f'get_kriteria: columns={cols}')
        df = pd.DataFrame(rows, columns=cols)
        _log(f'get_kriteria: dataframe shape={getattr(df, "shape", None)}')
        cur.close()
        conn.close()
        return df
    except Exception:
        _log('get_kriteria: exception')
        with open(os.path.join(os.path.dirname(__file__), 'spk_debug.log'), 'a', encoding='utf-8') as f:
            traceback.print_exc(file=f)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        raise

def get_matrix():
    conn = get_connection()

    query = """
        SELECT
            a.kode AS kode_alternatif,
            a.nama AS nama_alternatif,
            k.kode AS kode_kriteria,
            n.nilai
        FROM nilai_alternatif n
        JOIN alternatif a ON n.alternatif_id = a.id
        JOIN kriteria k ON n.kriteria_id = k.id
        ORDER BY a.id, k.id
    """

    _log('get_matrix: start')
    cur = conn.cursor()
    _log('get_matrix: executing query')
    cur.execute(query)
    _log('get_matrix: fetched rows')
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    df = pd.DataFrame(rows, columns=cols)
    _log(f'get_matrix: df shape={getattr(df, "shape", None)}')
    cur.close()
    conn.close()

    matrix = df.pivot_table(
        index=["kode_alternatif", "nama_alternatif"],
        columns="kode_kriteria",
        values="nilai"
    ).reset_index()

    return matrix

@app.route("/")
def index():

    # Ambil data
    kriteria = get_kriteria()
    matrix_data = get_matrix()

    # Kode kriteria
    kode_kriteria = kriteria["kode"].tolist()

    # Simpan info alternatif
    alt_info = matrix_data[["kode_alternatif", "nama_alternatif"]].copy()

    # Matriks keputusan
    X = matrix_data[kode_kriteria].apply(pd.to_numeric, errors="coerce")

    pembagi = np.sqrt((X ** 2).sum(axis=0))
    R = X / pembagi

    bobot_awal = pd.to_numeric(kriteria["bobot_awal"], errors="coerce")
    total_bobot = bobot_awal.sum()

    kriteria["bobot"] = bobot_awal / total_bobot

    W = pd.Series(
        kriteria["bobot"].values,
        index=kriteria["kode"].values
    )

    Y = R * W

    ideal_pos = {}
    ideal_neg = {}

    for col in Y.columns:

        tipe = kriteria.loc[
            kriteria["kode"] == col,
            "tipe"
        ].values[0]

        if tipe == "benefit":
            ideal_pos[col] = Y[col].max()
            ideal_neg[col] = Y[col].min()
        else:
            ideal_pos[col] = Y[col].min()
            ideal_neg[col] = Y[col].max()

    ideal_pos_series = pd.Series(ideal_pos)
    ideal_neg_series = pd.Series(ideal_neg)

    D_pos = np.sqrt(((Y - ideal_pos_series) ** 2).sum(axis=1))
    D_neg = np.sqrt(((Y - ideal_neg_series) ** 2).sum(axis=1))

    V = D_neg / (D_pos + D_neg)

    hasil = alt_info.copy()

    hasil["D_plus"] = D_pos
    hasil["D_minus"] = D_neg
    hasil["V"] = V

    hasil = hasil.sort_values(by="V", ascending=False)

    hasil["Ranking"] = range(1, len(hasil) + 1)

    X_html = pd.concat([alt_info, X], axis=1).to_html(index=False)
    R_html = pd.concat([alt_info, R], axis=1).to_html(index=False)
    Y_html = pd.concat([alt_info, Y], axis=1).to_html(index=False)

    ideal_df = pd.DataFrame({
        "Kriteria": kode_kriteria,
        "A_plus": [ideal_pos[c] for c in kode_kriteria],
        "A_minus": [ideal_neg[c] for c in kode_kriteria]
    })

    distance_df = pd.DataFrame({
        "Alternatif": matrix_data["nama_alternatif"],
        "D_plus": D_pos,
        "D_minus": D_neg,
        "V": V
    })

    return render_template(
        "index.html",
        X=X_html,
        R=R_html,
        Y=Y_html,
        ideal=ideal_df.to_html(index=False),
        distance=distance_df.to_html(index=False),
        result=hasil.to_html(index=False)
    )

if __name__ == "__main__":
    app.run(debug=True)
