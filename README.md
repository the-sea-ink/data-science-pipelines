This is a TU-Berlin Master's Thesis. It is created and implemented for research and educational purposes only, not for commercial use.

To begin with, install the requirements:
```
python -m pip install -r requirements.txt
```
Switch to virtual environment and install Regraph by executing following command inside the third_library/Regraph folder:
```
python setup.py install
```

To use CLI:
1. start virtual environment
2. cd into the project folder data-science-pipelines
3. run commands

Commands: 
```
initialize database:    python data_science_pipelines init_db 
create pipeline:        python data_science_pipelines create_pipeline path_to_script language --hpath hook_path --wtfile True --opath output_file_path 
extract rule:           python data_science_pipelines extract_rule path_to_g1 path_to_g2 rule_type 
confirm rule:           python data_science_pipelines path_to_pattern path_to_result rule_name rule_description language rule_type rule_priority
list rules by language: python data_science_pipelines list_rules language 
visualize rule:         python data_science_pipelines visualize_rule rule_name 
delete a rule:          python data_science_pipelines delete_rule rule_name
add a rule:             python data_science_pipelines add_rule path_to_rule
add new module to kb:   python data_science_pipelines add_module module_name module_version date(yyyy-mm-dd) language
add function to kb:     python data_science_pipelines add_function module_name function_title function_description function_language ds_task --dlink link_to_documentation
add data science dask:  python data_science_pipelines add_ds_task module_name function_title language ds_task 
add description:        python data_science_pipelines add_description module_name function_title language description 
```






To populate our knowledge base, we used publicly available information from [Pandas](https://pandas.pydata.org/docs/) (BSD-3-Clause license) and [Scikit-learn](https://scikit-learn.org/stable/modules/classes.html) (BSD-3-Clause license) documentation. We also used some of the data provided by the [Data Science Ontology](https://github.com/IBM/datascienceontology) project (CC-BY-4.0 license). 

