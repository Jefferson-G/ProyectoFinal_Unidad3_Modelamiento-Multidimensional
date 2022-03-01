import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from datetime import datetime
import psycopg2

def log(logfile, message):
    timestamp_format = '%H:%M:%S-%h-%d-%Y'
    #Hour-Minute-Second-MonthName-Day-Year
    now = datetime.now() # get current timestamp
    timestamp = now.strftime(timestamp_format)
    with open(logfile,"a") as f: 
        f.write('[' + timestamp + ']: ' + message + '\n')
        print(message)

def transform():

    log(logfile, "-------------------------------------------------------------")
    log(logfile, "Inicia Fase De Transformacion")
    df_orders_fact = pd.read_sql_query("""
      SELECT OrderDetail.Id AS FactId,
       Customer.Id AS CustomerId,
       Employee.Id AS EmployeeId,
       Customer.Id AS LocationId,
       strftime('%Y%m%d', datetime([Order].OrderDate)) as TimeId, 
       Product.Id AS ProductId,
       Shipper.Id AS ShipperId,
       OrderDetail.UnitPrice,
       OrderDetail.Quantity,
       OrderDetail.Discount
         FROM OrderDetail
        INNER JOIN [Order]  ON [Order].Id = OrderDetail.OrderId 
        INNER JOIN Customer  ON Customer.Id = [Order].CustomerId
        INNER JOIN Employee  ON Employee.Id = [Order].EmployeeId 
        INNER JOIN Shipper  ON Shipper.Id = [Order].ShipVia 
        INNER JOIN Product  ON Product.Id = OrderDetail.ProductId;
        """, con=engine.connect())

    df_customers = pd.read_sql_query("""SELECT Id AS CustomerId, 
        CompanyName, 
        ContactName, 
        ContactTitle, 
        Address, 
        City, 
        Region, 
        CASE
           WHEN PostalCode is NOT NULL then PostalCode
        ELSE 'NA'
        END
        PostalCode,
        Country, 
        Phone,
        CASE
           WHEN Fax is NOT NULL then Fax
        ELSE 'NA'
        END
        Fax
        FROM Customer;
        """, con=engine.connect())
    df_employees = pd.read_sql_query("""
       SELECT Id AS EmployeeId,
       LastName,
       FirstName,
       Title,
       TitleOfCourtesy,
       BirthDate,
       HireDate,
       Address,
       City,
       Region,
       PostalCode,
       Country,
       HomePhone,
       Extension,
       CASE
           WHEN Photo is NOT NULL then Photo
        ELSE 'foto no registrada'
        END
        Photo,
       Notes,
       PhotoPath
        FROM Employee;
        """, con=engine.connect())
    df_location = pd.read_sql_query("""
       SELECT Id AS LocationId,
       Address,
       City,
       Region,
       CASE
           WHEN PostalCode is NOT NULL then PostalCode
        ELSE 'NA'
        END
        PostalCode,
       Country
       FROM Customer;
        """, con=engine.connect())
    df_product = pd.read_sql_query("""
       SELECT p.Id AS ProductId,
       p.ProductName,
       p.QuantityPerUnit,
       p.UnitPrice,
       p.UnitsInStock,
       p.UnitsOnOrder,
       p.ReorderLevel,
       p.Discontinued
       FROM Product p;
        """, con=engine.connect())
    df_shipper = pd.read_sql_query("""
    SELECT Id AS ShipperId,
       CompanyName,
       Phone
     FROM Shipper;""", con=engine.connect())
     
    df_category = pd.read_sql_query("""
       SELECT Id AS CategoryId,
       CategoryName,
       Description
       FROM Category;
        """, con=engine.connect())
    
    df_supplier = pd.read_sql_query("""
       SELECT Id AS SupplierId,
       CompanyName,
       ContactName,
       ContactTitle,
       Address,
       City,
       Region,
       PostalCode,
       Country,
       Phone,
       CASE
           WHEN Fax is NOT NULL then Fax
        ELSE 'NA'
        END
        Fax,
       CASE
           WHEN  HomePage is NOT NULL then  HomePage
        ELSE 'NA'
        END
         HomePage
       FROM Supplier;
        """, con=engine.connect())

    log(logfile, "Finaliza Fase De Transformacion")
    log(logfile, "-------------------------------------------------------------")
    return df_orders_fact,df_customers,df_employees,df_location,df_product,df_shipper,df_category,df_supplier
   
def load():
    """ Connect to the PostgreSQL database server """
    conn_string = 'postgresql://postgres:12345@localhost:5433/DW_Northwind_CopoN'
    db = create_engine(conn_string)
    conn = db.connect()
    try:
        log(logfile, "-------------------------------------------------------------")
        log(logfile, "Inicia  Carga")
        df_customers.to_sql('dim_customer', conn, if_exists='append',index=False)
        df_employees.to_sql('dim_employee', conn, if_exists='append',index=False)
        df_location.to_sql('dim_location', conn, if_exists='append',index=False)
        df_product.to_sql('dim_product', conn, if_exists='append',index=False)
        df_category.to_sql('dim_category', conn, if_exists='append',index=False)
        df_supplier.to_sql('dim_supplier', conn, if_exists='append',index=False)
        df_shipper.to_sql('dim_shipper', conn, if_exists='append',index=False)
        df_orders_fact.to_sql('orders_fact', conn, if_exists='append',index=False)
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()
        log(logfile, "Finaliza Carga")
        log(logfile, "-------------------------------------------------------------")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally: 
        if conn is not None:
            conn.close()
            print('Conexion de la base de datos cerrada.')

def extract():
    log(logfile, "--------------------------------------------------------")
    log(logfile, "Inicia Extraccion")
    metadata = MetaData()
    metadata.create_all(engine)
    log(logfile, "Finaliza Extraccion")
    log(logfile, "--------------------------------------------------------")


if __name__ == '__main__':
    
    logfile = "ProyectoETL_logfile.txt"
    log(logfile, "ETL iniciado.")
    engine = create_engine('sqlite:///Northwind.sqlite')
    extract()
    (df_orders_fact,df_customers,df_employees,df_location,df_product,df_shipper,df_category,df_supplier) = transform()
    load()
    log(logfile, "ETL  finalizado.")
