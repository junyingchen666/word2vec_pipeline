from fabric.api import local

target = "w2v_pipeline/predict.py"

def push():
    local('git commit -a')
    local('git push')

def run():
    local("python {}".format(target))

def edit():
    local("emacs {} &".format(target))

def view():
    #local("sqlitebrowser data_sql/PLoS_bio.sqlite")
    local("sqlitebrowser data_parsed/PLoS_bio.sqlite")

def import_data():
    local("python w2v_pipeline/import_data.py")
    local("python w2v_pipeline/phrases_from_abbrs.py")  

def train():
    local("python w2v_pipeline/train.py")

def parse():
    local("python w2v_pipeline/parse.py")

def predict():
    local("python w2v_pipeline/predict.py")

def test():
    clean()
    
    import_data()
    parse()
    train()
    predict()

def clean():
    local('find . -name "*~" | xargs -I {} rm {}')
    local("rm -rf data_sql data_parsed collated")

    

