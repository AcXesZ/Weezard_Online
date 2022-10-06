import pandas as pd
import jinja2

with open('prod_all.csv', 'w') as f:
    f.writelines('store location, store zip, name, strain, grower, type, price, weight, thc%, total mg, cost/mg\n')

with open('prod_dut.csv', 'r') as f:
    prod_list_dut = f.readlines()
    prod_list_dut = [line.rstrip() for line in prod_list_dut]
    prod_list_dut = list(set(prod_list_dut))
    print(f'Dutchie has {len(prod_list_dut)} entries.')

with open('prod_ihj.csv', 'r') as f:
    prod_list_ihj = f.readlines()
    prod_list_ihj = [line.rstrip() for line in prod_list_ihj]
    prod_list_ihj = list(set(prod_list_ihj))
    print(f'IHJ has {len(prod_list_ihj)} entries.')

with open('prod_sun.csv', 'r') as f:
    prod_list_sun = f.readlines()
    prod_list_sun = [line.rstrip() for line in prod_list_sun]
    prod_list_sun = list(set(prod_list_sun))
    print(f'SUN has {len(prod_list_sun)} entries.')

prod_list_master = prod_list_dut
prod_list_master += prod_list_ihj
prod_list_master += prod_list_sun

print(len(prod_list_master))


def csv_write_row(prod_row):
    with open('prod_all.csv', 'a') as f_prods:
        f_prods.writelines(f'{prod_row}\n')


for row in prod_list_master:
    csv_write_row(row)


def html_write():
    df1 = pd.read_csv('prod_all.csv')
    df1.drop_duplicates(inplace=True)
    df1.style.format(precision=3)

    df1.columns = ['Store Location',
                   'Store Zip',
                   'Name',
                   'Strain',
                   'Grower',
                   'Type',
                   'Price',
                   'Weight',
                   'THC%',
                   'THC mg',
                   '$/mg',
                   ]
    del df1[df1.columns[0]]
    # print("The dataframe is:")
    # print(df1)

    html_string = ''
    html_string += df1.to_html(escape=False)
    html_string = html_string.replace('<table', '<table id="table_id"')

    env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))
    t = env.get_template("template.html")
    rendered_template = t.render(body=html_string)

    with open('prod_table.html', 'w') as f_html:
        f_html.write(rendered_template)


if __name__ == '__main__':
    html_write()
