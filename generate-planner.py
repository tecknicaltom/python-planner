import requests as req
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from datetime import date as new_date
import calendar

import fpdf


class Iterator:
    """
    Simple iterator class. Just has_next(), get_next() and peek()
    """

    def __init__(self, lst):
        self.list = lst
        self.index = 0

    def has_next(self):
        return self.index < len(self.list) - 1

    def peek(self):
        return self.list[self.index]

    def get_next(self):
        self.index += 1
        return self.list[self.index - 1]


def add_holiday(date, day_x, day_y):
    """
    adds a holiday to the first row or the month if it's the first day of the month
    """

    if date.day == 1:
        pdf.set_font(style="", size=14)
        pdf.set_text_color(200)
        pdf.set_xy(day_x, day_y)
        pdf.cell(text=date.strftime("%B %Y"))
        pdf.set_text_color(0)

    if date in holidays:
        pdf.set_font(style="", size=14)
        pdf.set_text_color(200)
        pdf.set_xy(day_x, day_y)
        if date.day == 1:
            pdf.set_xy(day_x, day_y + row_spacing)
        pdf.cell(text=holidays[date])
        pdf.set_text_color(0)


# general constants
YEAR = 2024
include_mini_cal = True
extra_rows_first_day_of_week = 3  # extra rows for first day of the week
rows_per_day = 6
font = "helvetica"
import_fed_holidays = True
first_day_of_week = calendar.SUNDAY
highlight_weekend = True

# NOTE: does not support two holidays on one day
holidays = {}

if import_fed_holidays:
    # This is probably more complicated than it's worth, but I got bored
    # Collects table with holidays from site then converts to pandas dataframe
    df = pd.read_html(
        str(
            BeautifulSoup(
                req.get(
                    "https://www.officeholidays.com/countries/usa/" + str(YEAR)
                ).content,
                "html.parser",
            ).find_all("table")
        )
    )[0]

    for _, row in df.iterrows():
        holidays[
            datetime.strptime(row["Date"] + " " + str(YEAR), "%b %d %Y").date()
        ] = row["Holiday Name"].replace("in lieu", "observed")

# layout constants
indent_padding = 15  # smaller lines for each date padding
day_horizontal_spacing = 8  # horizontal space between days
vertical_padding = day_horizontal_spacing
horizontal_padding = vertical_padding

pdf = fpdf.FPDF(orientation="l")
pdf.set_margin(0)
pdf.set_font(family=font)

# Compute more constants
day_height = (pdf.h - vertical_padding * 2) / 4
day_width = (pdf.w - horizontal_padding * 2 - day_horizontal_spacing) / 2
row_spacing = day_height / (rows_per_day + 1)
links = dict()  # date to page links
cw = row_spacing * 6.5  # mini calendar width
ch = row_spacing * 5  # mini calendar height
crh, ccw = ch / 8, cw / 7  # mini calendar row height and column width
cx, cy = (
    pdf.w - horizontal_padding - cw,
    pdf.h - vertical_padding - ch,
)  # mini calendar x and y

# Get all dates in a year - there probably exists a more efficient way
# dates_with_dup contains full weeks for each month (even when month doesn't start on monday and end on sunday)
# so there are duplicated dates
dates_with_dup = [
    i
    for m in range(1, 13)
    for i in calendar.Calendar(firstweekday=first_day_of_week).itermonthdates(YEAR, m)
]
dates = []
for date in dates_with_dup:
    if date not in dates:
        dates.append(date)
date_iter = Iterator(dates)

# Add title page
pdf.add_page()
pdf.set_font(style="B", size=30)
pdf.set_y(pdf.h / 2)
pdf.cell(
    text=str(YEAR) + " PLANNER", center=True, new_x=fpdf.XPos.LEFT, new_y=fpdf.YPos.NEXT
)
pdf.set_font(style="", size=15)
pdf.cell(
    text="https://github.com/jpperret/python-planner",
    link="https://github.com/jpperret/python-planner",
    center=True,
)

while date_iter.has_next():
    pdf.add_page()
    page_link = pdf.add_link()
    pdf.set_link(page_link, page=pdf.page)

    first_date_of_week = date_iter.peek()

    # add week title
    pdf.set_font(style="B", size=20)
    pdf.set_xy(0, vertical_padding * 1.5)
    pdf.multi_cell(
        w=horizontal_padding + day_horizontal_spacing + day_width,
        align="C",
        text=first_date_of_week.strftime("Week Beginning %B %d, %Y"),
    )

    # Have to do all of left side before right side
    for i in range(1, 4):
        date = date_iter.get_next()
        links[date] = page_link

        x = horizontal_padding

        # Add shading behind Saturday and Sunday
        if highlight_weekend:
            if date.weekday() in {calendar.SATURDAY, calendar.SUNDAY}:
                pdf.set_fill_color(240)
                if i == 1:
                    pdf.set_xy(
                        x,
                        vertical_padding
                        + day_height * i
                        - extra_rows_first_day_of_week * row_spacing,
                    )
                    pdf.cell(
                        day_width,
                        day_height + extra_rows_first_day_of_week * row_spacing,
                        text="",
                        fill=True,
                    )
                else:
                    pdf.set_xy(x, vertical_padding + day_height * i)
                    pdf.cell(day_width, day_height, text="", fill=True)

        # Add lines to separate days
        pdf.set_line_width(0.3)
        pdf.set_draw_color(0)
        line_y = (
            vertical_padding
            + day_height * i
            - extra_rows_first_day_of_week * row_spacing * (i == 1)
        )
        pdf.line(x, line_y, x + day_width, line_y)
        if i == 3:
            line_y = vertical_padding + day_height * (i + 1)
            pdf.line(x, line_y, x + day_width, line_y)

        # Add day of week label
        pdf.set_font(style="", size=15)
        pdf.set_xy(
            x,
            vertical_padding
            + day_height * i
            + 11
            - extra_rows_first_day_of_week * row_spacing * (i == 1),
        )
        pdf.cell(w=indent_padding, align="C", text=date.strftime("%a"))

        # Add day of month label
        pdf.set_font(style="B", size=25)
        pdf.set_xy(
            x,
            vertical_padding
            + day_height * i
            + 2
            - extra_rows_first_day_of_week * row_spacing * (i == 1),
        )
        pdf.cell(w=indent_padding, align="C", text=str(date.day))

        add_holiday(
            date,
            x + indent_padding + 1,
            vertical_padding
            + day_height * i
            + 1
            - extra_rows_first_day_of_week * row_spacing * (i == 1),
        )

        # add daily lines
        pdf.set_draw_color(100)
        pdf.set_line_width(0.1)
        for line in range(1, rows_per_day + 1):
            line_y = vertical_padding + day_height * i + row_spacing * line
            pdf.line(x + indent_padding, line_y, x + day_width, line_y)
            if i == 1:
                # Add extra rows for first day of the week
                for extra_line in range(extra_rows_first_day_of_week + 1):
                    line_y = (
                        vertical_padding
                        + day_height
                        + row_spacing * extra_line
                        - extra_rows_first_day_of_week * row_spacing
                    )
                    pdf.line(
                        x + indent_padding,
                        line_y,
                        x + day_width,
                        line_y,
                    )

    # Add date labels on right
    for i in range(4):
        date = date_iter.get_next()
        links[date] = page_link

        x = horizontal_padding + day_horizontal_spacing + day_width

        # Add shading behind Saturday and Sunday
        if highlight_weekend:
            if date.weekday() in {calendar.SATURDAY, calendar.SUNDAY}:
                pdf.set_fill_color(240)
                pdf.set_xy(
                    x,
                    vertical_padding + day_height * i,
                )
                pdf.cell(day_width, day_height, text="", fill=True)

        # Add lines to separate days
        pdf.set_line_width(0.3)
        pdf.set_draw_color(0)
        line_y = vertical_padding + day_height * i
        pdf.line(x, line_y, x + day_width, line_y)
        if i == 3:
            line_y = vertical_padding + day_height * (i + 1)
            pdf.line(x, line_y, x + day_width, line_y)

        # Add day of week label
        pdf.set_font(style="", size=15)
        pdf.set_xy(
            x,
            vertical_padding + day_height * i + 11,
        )
        pdf.cell(w=indent_padding, align="C", text=date.strftime("%a"))

        # Add day of month label
        pdf.set_font(style="B", size=25)
        pdf.set_xy(
            x,
            vertical_padding + day_height * i + 2,
        )
        pdf.cell(w=indent_padding, align="C", text=str(date.day))

        add_holiday(
            date,
            x + indent_padding + 1,
            vertical_padding + day_height * i + 1,
        )

        # add daily lines
        pdf.set_draw_color(100)
        pdf.set_line_width(0.1)
        for line in range(1, rows_per_day + 1):
            line_y = vertical_padding + day_height * i + row_spacing * line
            pdf.line(x + indent_padding, line_y, x + day_width, line_y)

    if include_mini_cal:  # insert month overview in bottom right corner
        # set grey background
        pdf.set_xy(cx, cy)
        pdf.set_fill_color(250)
        # I would like a thicker border, but it's not supported
        pdf.cell(cw, ch, text="", fill=True, border=1)

        # Get first date for mini calendar
        # If month changes on thurs then use next month
        first_date_of_month = dates[dates.index(first_date_of_week) + calendar.THURSDAY]
        # Get first day of month to start mini calendar
        index_start_calendar = max(
            dates.index(first_date_of_month) - first_date_of_month.day + 1, 0
        )
        # Get calendar month. If before year starts then use January
        cal_month = (
            dates[index_start_calendar].month
            if dates[index_start_calendar].year == YEAR
            else 1
        )
        # get the first day of the week
        while dates[index_start_calendar].weekday() != first_day_of_week:
            index_start_calendar -= 1

        if (index_start_calendar + 6 * 7) < len(dates) and dates[
            index_start_calendar + 5 * 7
        ].month == cal_month:
            weeks_in_month = 6
        else:
            weeks_in_month = 5

        crh = ch / (weeks_in_month + 2)

        # Add month header
        pdf.set_font(style="", size=10)
        pdf.set_xy(cx, cy)
        pdf.cell(w=cw, text=new_date(YEAR, cal_month, 1).strftime("%B"), align="C")

        # Add weekday headers
        for c in range(7):
            pdf.set_xy(cx + ccw * c, cy + crh)
            pdf.cell(
                text=["M", "T", "W", "T", "F", "S", "S"][(c + first_day_of_week) % 7]
            )

        # Add dates and links to page
        for r in range(weeks_in_month):
            for c in range(7):  # 7 days in a week
                # Check if index is valid
                if index_start_calendar >= len(dates):
                    break

                link = pdf.add_link()
                # page number divided by 7 for week. Add 2 for rounding down and title page
                page = int(index_start_calendar / 7) + 2
                pdf.set_link(link, page=page)
                if dates[index_start_calendar].month != cal_month:
                    pdf.set_text_color(200)

                pdf.set_xy(
                    cx + ccw * c, cy + crh * (r + 2)
                )  # + 2 to skip month and weekday headers
                pdf.cell(
                    text=str(dates[index_start_calendar].day), link=link, align="C"
                )
                pdf.set_text_color(0)

                # Add a border around current week
                if dates[index_start_calendar] == first_date_of_week:
                    # (ccw / 10) is one half the padding in the rectangle (width = cw - ccw / 5)
                    # (r + 2) to skip month and weekday headers -.1 to center
                    pdf.set_xy(cx + ccw * c + (ccw / 10), cy + crh * (r + 2 - 0.1))
                    pdf.cell(w=cw - ccw / 5, h=crh, border=True)

                index_start_calendar += 1

pdf.output(str(YEAR) + " Planner.pdf")
