# Enter your code with the code smell here.

def main():
    import sqlite3

    try :
        connection = sqlite3.connect('src/python/data/database.sqlite')
        cursor = connection.cursor()

        REQUEST = """
            SELECT  EmployeeName, JobTitle, Benefits, TotalPayBenefits, Year
            FROM Salaries 
            WHERE BasePay >= 5000
            """
        
        cursor.execute(REQUEST)
        _ = cursor.fetchall()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":    
    main()