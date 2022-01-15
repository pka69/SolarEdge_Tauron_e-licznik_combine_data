import sys

import argparse

from Energy import OUTPUT_DIR, set_debug, debug, switch_debug, get_debug
from Energy.my_energy_reports import create_energy_reports
from Energy.subProjection.my_projection import create_monthly_projection


PERIODS_CONVERTER = {
    'daily': 'day(s)',
    'weekly': 'week(s)',
    'monthly': 'month(s)'
}
#
# define commandline parser
#
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", help="switch on debug messages",
                    action="store_true")
parser.add_argument("-r", "--refresh", help="action refresh data from API",
                    action="store_true")
parser.add_argument("-f", "--flash", help="add daily flash page to the report",
                    action="store_true")
parser.add_argument("-t", "--table", help="add pure table data to the report",
                    action="store_true")
parser.add_argument('-b', '--back', type=float, default=0.2, help='energy back cost(default 0.2)')
parser.add_argument('-k', '--kWh_cost', type=float, default=0.65, help='calculation kW cost (default=0.65 PLN)')
parser.add_argument("-p", "--projection", type=int, help="projection n-month production forward, integer value")
parser.add_argument("-g", "--group", default='daily', help="grouping param(daily, weekly, monthly), default daily")
parser.add_argument('-l', '--limits', default='', help='range of periods to report (format 2021/08-2022/02')
# try
args = parser.parse_args()
# except SystemExit as E:
#     # print('----------------------\nwystąpił bład w parametrach - {}\n----------------------'.format(E))
#     parser.print_help(sys.stderr)
#     sys.exit()
# except TypeError as E:
#     # print('----------------------\nwystąpił bład w parametrach - {}\n----------------------'.format(E))
#     parser.print_help(sys.stderr)
#     sys.exit()
#
# if no args print message and stop program
#
# if len(sys.argv) == 1:
#     parser.print_help(sys.stderr) 
#     sys.exit()
#
# check params and print start settings
#
print('----------------------\nstart settings\n----------------------')
print('- debug messages switched {}'.format('on' if args.debug else 'off'))
set_debug(args.debug)
print('- refresh data from API -  {}'.format('yes' if args.refresh else 'no'))
print('- add flesh report -  {}'.format('yes' if args.flash else 'no'))
print('- add pure table in the  report -  {}'.format('yes' if args.table else 'no'))
print('- energy back cost -  {:4.2f}'.format(args.back))
print('- kW cost -  {:4.2f} PLN'.format(args.kWh_cost))
if args.projection:
    print('- projection {} month{} production'.format(args.projection, 's' if args.projection>1 else ''))
print('- {} reports'.format(args.group))
if args.limits:
    periods = args.limits.split('-')
    if len(periods)!=2 or any([x.find('/')==-1 for x in periods]):
        print('błędnie podany zakres okresów')
        sys.exit()
    print('- periods limited to range {} - {} {}'.format(periods[0], periods[1], PERIODS_CONVERTER[args.group]))
else:
    print('- periods are not limited')
#
# run main application
#
energy_object, pdf = create_energy_reports(
    refresh = args.refresh,
    group = args.group,
    export_back = 1 - args.back,
    kWh_cost = args.kWh_cost,
    limit_periods = periods if args.limits else None
)
pdf.set_author("Piotr Kalista")
pdf.set_creator("energy reports.py")
pdf.set_title("PV energy report")
if args.flash:
    energy_object.daily_flash_page(pdf=pdf)

energy_object.group_report_pages(pdf=pdf, group_by=PERIODS_CONVERTER[args.group], table_include=args.table)

if args.projection:
    create_monthly_projection(energy_object, args.projection, pdf=pdf)
    
pdf.output('{}{:%Y%m%d}-{:%Y%m%d}-energy_report.pdf'.format(OUTPUT_DIR, energy_object.start_date, energy_object.stop_date), 'F') 
print('report created in {}{:%Y%m%d}-{:%Y%m%d}-energy_report.pdf'.format(OUTPUT_DIR, energy_object.start_date, energy_object.stop_date))
    
