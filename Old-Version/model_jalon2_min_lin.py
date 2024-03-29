"""
Implementation de la contrainte d'occupation des voies au chantier de formation
en linéarisant l'expression du minimum entre les wagons apportés par les trains à l'arrivée
"""
from gurobipy import *

from util import DepartsColumnNames
from lecture_donnees import DATA_DICT, DEPARTS, composition_train_depart
from model import linearise_abs

VAR_NAME_COUNTER = 0

def linearise_min(elt_1, elt_2, model, variables, contraintes):
    """
    linéarise l'expression `min(elt_1, elt2)` et renvoie l'expression linéaire associée
    """
    global VAR_NAME_COUNTER
    middle = elt_1 + elt_2
    to_abs = elt_1 - elt_2
    try:
        name_el1 = elt_1.VarName.replace("T", "t")
    except:
        name_el1 = f"lin_expr_in_linearise_min_{VAR_NAME_COUNTER}"
        VAR_NAME_COUNTER += 1
    try:
        name_el2 = elt_2.VarName.replace("T", "t")
    except:
        name_el2 = f"lin_expr_in_linearise_min_{VAR_NAME_COUNTER}"
        VAR_NAME_COUNTER += 1
    dist = linearise_abs(model, to_abs, f"dist_{name_el1}_{name_el2}",
                         variables=variables, contraintes=contraintes)
    return (middle - dist) / 2

def linearise_min_list(expr_list, model, variables, contraintes):
    """
    linéarise l'expression `min(expr_list)` et renvoie l'expression linéaire associée
    """
    length = len(expr_list)
    # traiter les cas limites
    if length == 0:
        return expr_list
    if length == 1:
        return expr_list[0]
    # cas général
    current_min_expr = linearise_min(expr_list[0], expr_list[1], model, variables, contraintes)
    for i in range(2, length):
        current_min_expr = linearise_min(current_min_expr, expr_list[i], model, variables, contraintes)
    return current_min_expr


def model_jalon2_min_lin(model, variables, contraintes):
    """
    Implementation du minimum pour le premier wagon
    arrivant au chantier FOR en linéarisant l'expression
    """
    for index in DEPARTS.index:
        jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
        numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
        train_arr_necessaires = [variables[f"Train_ARR_{jour_arr}_{numero_arr}_DEB"]
                                 for (jour_arr, numero_arr)
                                 in composition_train_depart(DATA_DICT, (jour, numero))]
        min_deb = linearise_min_list(train_arr_necessaires, model, variables, contraintes)
        mindeb_var_name = f"min_DEB_{jour}_{numero}"
        variables[mindeb_var_name] = model.addVar(vtype=GRB.INTEGER, lb=0, name=mindeb_var_name)
        contraintes["Constr_"+mindeb_var_name] = model.addConstr(variables[mindeb_var_name] == min_deb,
                                                                 name="Constr_"+mindeb_var_name)
