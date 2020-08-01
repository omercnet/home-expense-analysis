rm db.sqlite3
rm -rf expense/migrations visacal/migrations
./manage.py makemigrations expense visacal
./manage.py migrate
./manage.py loaddata expense/fixtures/categories.json
./manage.py createsuperuser
