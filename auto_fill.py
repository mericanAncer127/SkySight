import argparse
import ezdxf
import numpy as np
import pandas as pd
import os
from sketch_to_sheet import *
from sklearn.linear_model import LinearRegression

def main(folder):
    roof = Roof(folder, 6) # 6 is fontsize

    f = open(os.path.join(folder, "data_sheet.csv"))
    f.close()

    df = pd.read_csv(os.path.join(folder, "data_sheet.csv"))

    flat_lines = df.loc[df["Type (R, H, V, K, E)"].isin(["E", "R"])].copy()

    assert flat_lines["Length (ft.)"].value_counts()["-"] < flat_lines.shape[0], "No values entered"

    flat_lines["Drawing Length"] = [
        roof.get_line_by_id(_id).drawing_length for _id in flat_lines["Line Label"]]

    X, Y = [], []
    for i, row in flat_lines.iterrows():
        if row["Length (ft.)"] != "-":
            X.append(row["Drawing Length"])
            Y.append(row["Length (ft.)"])

    X, Y = np.array(X).reshape(-1, 1), np.array(Y).reshape(-1, 1)
    reg = LinearRegression().fit(X, Y)

    for i, row in flat_lines.iterrows():
        if row["Length (ft.)"] == "-":
            val = np.array([row["Drawing Length"]]).reshape(1, -1)
            pred = reg.predict(val)
            df.iat[i, 2] = int(pred[0][0])

    df.to_csv(os.path.join(folder, "data_sheet.csv"), index=False)
    f = open(os.path.join(folder, "data_sheet.csv"))
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--f", dest="folder")

    args = parser.parse_args()

    main(args.folder)
