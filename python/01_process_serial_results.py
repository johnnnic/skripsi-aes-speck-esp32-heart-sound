"""Process ESP32 Serial Monitor CSV output for AES-128 and SPECK testing.

Input:
    data/sample_serial/serial_output_75_rows.csv

Output:
    results/excel/01_Data_Raw_5x.xlsx
    results/excel/02_Statistik_Per_File.xlsx
    results/excel/03_Ringkasan_Kategori.xlsx
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = ROOT / "data" / "sample_serial" / "serial_output_75_rows.csv"
OUT_DIR = ROOT / "results" / "excel"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def kategori_file(no: int) -> str:
    if 1 <= no <= 5:
        return "Kecil"
    if 6 <= no <= 10:
        return "Sedang"
    return "Besar"


def tidy_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, data in sheets.items():
            data.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.sheets[sheet_name]
            ws.freeze_panes = "A2"
            for cell in ws[1]:
                cell.font = cell.font.copy(bold=True)
            for column_cells in ws.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter
                for cell in column_cells:
                    value = cell.value
                    if value is not None:
                        max_length = max(max_length, len(str(value)))
                ws.column_dimensions[column_letter].width = min(max_length + 2, 35)
            for row in ws.iter_rows():
                for cell in row:
                    if isinstance(cell.value, float):
                        cell.number_format = "0.00"


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    df_raw = pd.read_csv(INPUT_CSV)
    df_raw["File"] = df_raw["File"].str.replace("/", "", regex=False)
    df_raw["Kategori"] = df_raw["No"].apply(kategori_file)

    df_raw["AES Encrypt Throughput (KB/s)"] = (df_raw["AES Bytes"] / 1024) / (df_raw["AES Encrypt us"] / 1_000_000)
    df_raw["AES Decrypt Throughput (KB/s)"] = (df_raw["AES Bytes"] / 1024) / (df_raw["AES Decrypt us"] / 1_000_000)
    df_raw["SPECK Encrypt Throughput (KB/s)"] = (df_raw["SPECK Bytes"] / 1024) / (df_raw["SPECK Encrypt us"] / 1_000_000)
    df_raw["SPECK Decrypt Throughput (KB/s)"] = (df_raw["SPECK Bytes"] / 1024) / (df_raw["SPECK Decrypt us"] / 1_000_000)

    agg_dict = {
        "AES Bytes": "first",
        "SPECK Bytes": "first",
        "AES Encrypt us": ["mean", "std", "min", "max"],
        "AES Decrypt us": ["mean", "std", "min", "max"],
        "SPECK Encrypt us": ["mean", "std", "min", "max"],
        "SPECK Decrypt us": ["mean", "std", "min", "max"],
        "AES Encrypt Throughput (KB/s)": ["mean", "std", "min", "max"],
        "AES Decrypt Throughput (KB/s)": ["mean", "std", "min", "max"],
        "SPECK Encrypt Throughput (KB/s)": ["mean", "std", "min", "max"],
        "SPECK Decrypt Throughput (KB/s)": ["mean", "std", "min", "max"],
    }

    df_file = df_raw.groupby(["No", "File", "Kategori"], as_index=False).agg(agg_dict)
    df_file.columns = [" ".join(col).strip() if isinstance(col, tuple) else col for col in df_file.columns]

    rename_map = {
        "AES Bytes first": "AES Bytes",
        "SPECK Bytes first": "SPECK Bytes",
        "AES Encrypt us mean": "AES Encrypt Avg (us)",
        "AES Encrypt us std": "AES Encrypt Std (us)",
        "AES Encrypt us min": "AES Encrypt Min (us)",
        "AES Encrypt us max": "AES Encrypt Max (us)",
        "AES Decrypt us mean": "AES Decrypt Avg (us)",
        "AES Decrypt us std": "AES Decrypt Std (us)",
        "AES Decrypt us min": "AES Decrypt Min (us)",
        "AES Decrypt us max": "AES Decrypt Max (us)",
        "SPECK Encrypt us mean": "SPECK Encrypt Avg (us)",
        "SPECK Encrypt us std": "SPECK Encrypt Std (us)",
        "SPECK Encrypt us min": "SPECK Encrypt Min (us)",
        "SPECK Encrypt us max": "SPECK Encrypt Max (us)",
        "SPECK Decrypt us mean": "SPECK Decrypt Avg (us)",
        "SPECK Decrypt us std": "SPECK Decrypt Std (us)",
        "SPECK Decrypt us min": "SPECK Decrypt Min (us)",
        "SPECK Decrypt us max": "SPECK Decrypt Max (us)",
        "AES Encrypt Throughput (KB/s) mean": "AES Encrypt Throughput Avg (KB/s)",
        "AES Encrypt Throughput (KB/s) std": "AES Encrypt Throughput Std (KB/s)",
        "AES Encrypt Throughput (KB/s) min": "AES Encrypt Throughput Min (KB/s)",
        "AES Encrypt Throughput (KB/s) max": "AES Encrypt Throughput Max (KB/s)",
        "AES Decrypt Throughput (KB/s) mean": "AES Decrypt Throughput Avg (KB/s)",
        "AES Decrypt Throughput (KB/s) std": "AES Decrypt Throughput Std (KB/s)",
        "AES Decrypt Throughput (KB/s) min": "AES Decrypt Throughput Min (KB/s)",
        "AES Decrypt Throughput (KB/s) max": "AES Decrypt Throughput Max (KB/s)",
        "SPECK Encrypt Throughput (KB/s) mean": "SPECK Encrypt Throughput Avg (KB/s)",
        "SPECK Encrypt Throughput (KB/s) std": "SPECK Encrypt Throughput Std (KB/s)",
        "SPECK Encrypt Throughput (KB/s) min": "SPECK Encrypt Throughput Min (KB/s)",
        "SPECK Encrypt Throughput (KB/s) max": "SPECK Encrypt Throughput Max (KB/s)",
        "SPECK Decrypt Throughput (KB/s) mean": "SPECK Decrypt Throughput Avg (KB/s)",
        "SPECK Decrypt Throughput (KB/s) std": "SPECK Decrypt Throughput Std (KB/s)",
        "SPECK Decrypt Throughput (KB/s) min": "SPECK Decrypt Throughput Min (KB/s)",
        "SPECK Decrypt Throughput (KB/s) max": "SPECK Decrypt Throughput Max (KB/s)",
    }
    df_file = df_file.rename(columns=rename_map)

    df_file["Keunggulan Encrypt SPECK (%)"] = ((df_file["AES Encrypt Avg (us)"] - df_file["SPECK Encrypt Avg (us)"]) / df_file["AES Encrypt Avg (us)"]) * 100
    df_file["Keunggulan Decrypt SPECK (%)"] = ((df_file["AES Decrypt Avg (us)"] - df_file["SPECK Decrypt Avg (us)"]) / df_file["AES Decrypt Avg (us)"]) * 100

    df_kategori = df_file.groupby("Kategori", as_index=False).agg({
        "No": "count",
        "AES Bytes": "sum",
        "AES Encrypt Avg (us)": "mean",
        "AES Encrypt Std (us)": "mean",
        "AES Encrypt Min (us)": "mean",
        "AES Encrypt Max (us)": "mean",
        "SPECK Encrypt Avg (us)": "mean",
        "SPECK Encrypt Std (us)": "mean",
        "SPECK Encrypt Min (us)": "mean",
        "SPECK Encrypt Max (us)": "mean",
        "AES Decrypt Avg (us)": "mean",
        "AES Decrypt Std (us)": "mean",
        "AES Decrypt Min (us)": "mean",
        "AES Decrypt Max (us)": "mean",
        "SPECK Decrypt Avg (us)": "mean",
        "SPECK Decrypt Std (us)": "mean",
        "SPECK Decrypt Min (us)": "mean",
        "SPECK Decrypt Max (us)": "mean",
        "AES Encrypt Throughput Avg (KB/s)": "mean",
        "AES Decrypt Throughput Avg (KB/s)": "mean",
        "SPECK Encrypt Throughput Avg (KB/s)": "mean",
        "SPECK Decrypt Throughput Avg (KB/s)": "mean",
        "Keunggulan Encrypt SPECK (%)": "mean",
        "Keunggulan Decrypt SPECK (%)": "mean",
    }).rename(columns={"No": "Jumlah File", "AES Bytes": "Total Audio Bytes"})

    kategori_order = ["Kecil", "Sedang", "Besar"]
    df_kategori["Kategori"] = pd.Categorical(df_kategori["Kategori"], categories=kategori_order, ordered=True)
    df_kategori = df_kategori.sort_values("Kategori")
    df_kategori["Kategori"] = df_kategori["Kategori"].astype(str)

    total_row = {col: None for col in df_kategori.columns}
    total_row.update({
        "Kategori": "Total",
        "Jumlah File": df_file["No"].count(),
        "Total Audio Bytes": df_file["AES Bytes"].sum(),
    })
    for col in df_kategori.columns:
        if col not in {"Kategori", "Jumlah File", "Total Audio Bytes"}:
            total_row[col] = df_file[col].mean() if col in df_file.columns else None
    df_kategori = pd.concat([df_kategori, pd.DataFrame([total_row])], ignore_index=True)

    tidy_excel(OUT_DIR / "01_Data_Raw_5x.xlsx", {"Data_Raw_5x": df_raw})
    tidy_excel(OUT_DIR / "02_Statistik_Per_File.xlsx", {"Statistik_Per_File": df_file})
    tidy_excel(OUT_DIR / "03_Ringkasan_Kategori.xlsx", {"Ringkasan_Kategori": df_kategori})

    print("Jumlah data raw:", len(df_raw))
    print("Jumlah file:", df_file["File"].nunique())
    print("Kategori:", ", ".join(df_kategori["Kategori"].astype(str)))


if __name__ == "__main__":
    main()
