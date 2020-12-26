# -*- coding: utf-8 -*-
"""
Created on Thu Aug 13 16:50:19 2020

@author: Jesse Boise
"""

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import matplotlib
import matplotlib.pyplot as plt
import mysql.connector as mcon
import pandas as pd
import tkinter as tk
import tkinter.ttk as ttk

connect_args = {
    "host": "localhost",
    "user": "root",
    "passwd": "thisismypassword",
    "database": "covid-data"
}

class Country:
    ISO_Code = ""
    Name = ""

    def __init__(self, iso, name):
        self.ISO_Code = iso
        self.Name = name

    def __repr__(self):
        return f"{self.ISO_Code} ({self.Name})"

    @staticmethod
    def unpack_repr(value):
        return value[:3]

class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("CovidConvene")
        self.create_widgets()

    def create_widgets(self):
        self.main_frame = tk.Frame(self, bg="white")
        self.main_frame.pack(side="top", fill="both", expand=True)

        self.header_frame = tk.Frame(self.main_frame)
        self.header_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
        if self.header_frame:
            self.search_frame = tk.Frame(self.header_frame, bg="#fff")
            self.search_frame.pack(side="left", fill="x", padx=5, pady=5, ipadx=12, ipady=8)
            if self.search_frame:
                self.iso_label = tk.Label(self.search_frame, text="Select a country to load", )
                self.iso_label.pack()

                iso_data = get_iso_data()
                self.iso_select = ttk.Combobox(self.search_frame, values=iso_data)
                self.iso_select.pack(side=tk.TOP)

                self.isofilter_button = ttk.Button(self.search_frame, text="Update",
                                                    command=self.update_plot)
                self.isofilter_button.pack(side=tk.TOP, pady=5)

            self.data_viewtype = tk.StringVar()
            self.current_viewtype = ""

            self.viewtype_frame = tk.Frame(self.header_frame)
            self.viewtype_frame.pack(side=tk.LEFT, padx=12, pady=12)
            if self.viewtype_frame:
                self.viewtype_bar_rb = ttk.Radiobutton(self.viewtype_frame, text="Bar", variable=self.data_viewtype, value="bar",
                                                       command=self.adjust_viewtype)
                self.viewtype_bar_rb.pack(anchor=tk.W)

                self.viewtype_line_rb = ttk.Radiobutton(self.viewtype_frame, text="Line", variable=self.data_viewtype, value="line",
                                                        command=self.adjust_viewtype)
                self.viewtype_line_rb.pack(anchor=tk.W)

            self.summary_tcases = tk.StringVar()
            self.summary_ncases = tk.StringVar()
            self.summary_tdeaths = tk.StringVar()
            self.summary_ndeaths = tk.StringVar()

            self.summary_frame = tk.Frame(self.header_frame)
            self.summary_frame.pack(side=tk.RIGHT, ipadx=15)
            if self.summary_frame:
                # Total Cases Label
                self.summary_totalcases_label = ttk.Label(self.summary_frame,
                                                     textvariable=self.summary_tcases)
                self.summary_totalcases_label.pack(fill="x", expand=True)

                # New Cases Label
                self.summary_newcases_label = ttk.Label(self.summary_frame,
                                                     textvariable=self.summary_ncases)
                self.summary_newcases_label.pack(fill="x", expand=True)

                # Total Deaths Label
                self.summary_totaldeaths_label = ttk.Label(self.summary_frame,
                                                     textvariable=self.summary_tdeaths)
                self.summary_totaldeaths_label.pack(fill="x", expand=True)

                # New Deaths Label
                self.summary_newdeaths_label = ttk.Label(self.summary_frame,
                                                     textvariable=self.summary_ndeaths)
                self.summary_newdeaths_label.pack(fill="x", expand=True)


    def update_plot(self):
        if self.iso_select.current() == -1:
            return
        iso = Country.unpack_repr(self.iso_select.get())
        plotting = get_plot_data(iso)
        if hasattr(self, "covid_plot"):
            self.covid_plot.pack_forget()

        cols = get_columns_total(["total_cases", "new_cases", "total_deaths", "total_cases"], iso)
        self.summary_tcases.set(f"Total Cases: {cols[0]}")
        self.summary_ncases.set(f"New Cases: {cols[1]}")
        self.summary_tdeaths.set(f"Total Deaths: {cols[2]}")
        self.summary_ndeaths.set(f"New Deaths: {int(cols[3])}")

        self.covid_plot = self.create_matplotlib_plot(
            plotting["dates"],
            {x: plotting[x] for x in plotting if x != "dates"}
        )
        self.covid_plot.pack(side="top")

    def adjust_viewtype(self):
        if self.data_viewtype.get() != self.current_viewtype:
            self.current_viewtype = self.data_viewtype.get()
            self.update_plot()


    def create_matplotlib_plot(self, x, y):
        f = Figure(figsize=(9,7), dpi=100)
        ax = f.subplots(nrows=len(y), ncols=1)

        idx = 0
        for key in y:
            el1, el2 = zip(*y[key])
            ax[idx].set_title(key.capitalize())
            if self.data_viewtype.get() == "bar":
                ax[idx].bar(x, el2, color="b")
                ax[idx].bar(x, el1, color="r")
            elif self.data_viewtype.get() == "line":
                ax[idx].plot(x, el2, color="b")
                ax[idx].plot(x, el1, color="r")
            else:
                ax[idx].plot(x, el2, color="b")
                ax[idx].plot(x, el1, color="r")
            idx += 1
        f.legend(labels=(f"Totals to date", f"New ocurrence on date"))

        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()
        return canvas.get_tk_widget()

    def refresh_matplotlib_plot(self, x, y):
        self.covid_figure.clear()
        ax = self.covid_figure.subplots(nrows=len(y), ncols=1)

        idx = 0
        for key in y:
            el1, el2 = zip(*y[key])

            if self.data_viewtype.get() == "bar":
                ax[idx].bar(x, el1, color="r")
                ax[idx].bar(x, el2, color="b")
            elif self.data_viewtype.get() == "line":
                ax[idx].plot(x, el1, color="r")
                ax[idx].plot(x, el2, color="b")
            idx += 1

        canvas = FigureCanvasTkAgg(self.covid_figure, self)
        canvas.draw()
        return canvas.get_tk_widget()


def plot(x, y):
    fig, ax = plt.subplots(nrows=len(y), ncols=1)

    idx = 0
    for key in y:
        el1, el2 = zip(*y[key])

        ax[idx].bar(x, el1)
        ax[idx].bar(x, el2)
        idx += 1
    plt.show()


def get_iso_data():
    con = mcon.connect(**connect_args)
    cursor = con.cursor()

    cursor.execute("""
       SELECT DISTINCT(`ISO_CODE`), `COUNTRY_NAME`
       FROM `global-tolls`
   """)

    data = []
    for item in cursor.fetchall():
        data.append(Country(item[0], item[1]))
    return data
    # return list(zip(*cursor.fetchall()))[0]

def get_columns_total(columns, iso):
    if type(columns) is list:
        con = mcon.connect(**connect_args)
        cursor = con.cursor()

        cols = ",".join(map(
            lambda x: f"SUM({x})", columns
        ))

        cursor.execute(f"""
           SELECT {cols}
           FROM `global-tolls`
           WHERE `ISO_CODE` = %s
       """, (iso,))

        data = cursor.fetchall()
        return data[0]
    elif type(columns) is str:
        pass

def get_plot_data(iso):
    con = mcon.connect(**connect_args)
    cursor = con.cursor()

    cursor.execute("""
       SELECT *
       FROM `global-tolls`
       WHERE `ISO_CODE` = %s
   """, (iso,))

    data_cols = ["dates", "cases", "deaths"]
    plot_data = {x:[] for x in data_cols}

    day = cursor.fetchone()
    while day:
        date = day[3]
        new_cases = day[4]
        total_cases = day[5]
        new_deaths = day[6]
        total_deaths = day[7]

        plot_data["dates"].append(date)
        plot_data["cases"].append((new_cases, total_cases))
        plot_data["deaths"].append((new_deaths, total_deaths))

        day = cursor.fetchone()

    plot_df = pd.DataFrame(plot_data, columns=data_cols)
    return plot_df


if __name__ == "__main__":
    matplotlib.use("TkAgg")
    matplotlib.style.use("ggplot")

    app = Application()
    app.mainloop()