import re
import collections
import random
import graphviz
from functools import wraps, partial

def debug_method(func= None, prefix = ''):
    if func is None:
        return partial(debug, prefix = prefix)
    else:
        msg = prefix + func.__name__
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(msg)
            return func(*args,**kwargs)
        return wrapper

def debug_class(cls):
    for key, val in vars(cls).items():
        if callable(val):
            setattr(cls, key, debug_method(val))
        return cls

print("Evaluado el codigo")

separacion = 60

CONST     = r'(?P<CONST>[a-z][A-Z]*)'
NUM     = r'(?P<NUM>\d+)'
PLUS    = r'(?P<PLUS>\+)'
MINUS   = r'(?P<MINUS>-)'
OR    = r'(?P<OR>∨)'
AND   = r'(?P<AND>∧)'
NOT   = r'(?P<NOT>¬)'
TIMES   = r'(?P<TIMES>\*)'
DIVIDE  = r'(?P<DIVIDE>/)'
LPAREN  = r'(?P<LPAREN>\()'
RPAREN  = r'(?P<RPAREN>\))'
WS      = r'(?P<WS>\s+)'
VERDADERO  = r'(?P<VERDADERO>TRUE)'
FALSO  = r'(?P<FALSO>FALSE)'

master_pattern = re.compile('|'.join((CONST,NUM, PLUS, MINUS, OR, AND, NOT,
                                       TIMES, DIVIDE, LPAREN, RPAREN, WS,
                                       VERDADERO, FALSO)))
Token = collections.namedtuple('Token', ['type', 'value'])


def lista_tokens(pattern, text):
    scanner = pattern.scanner(text)
    for m in iter(scanner.match, None):
        token = Token(m.lastgroup, m.group())

        if token.type != 'WS':
            yield token

print(list(lista_tokens(master_pattern,'x ∨ y v z' )))


class SentenciaBooleana:
    '''
    Pequeña implementación de un parser de formulaesiones booleanas.
    Implementation of a recursive descent parser.
    Aquí la asignacion es un diccionario con variables.
    '''

    def parse(self, text, asig):
        self.text = text
        self.tokens = lista_tokens(master_pattern, text)
        self.current_token = None
        self.next_token = None
        self._avanza()
        self.asig = asig
        return self.formula()

    def _avanza(self):
        self.current_token, self.next_token = self.next_token, next(self.tokens, None)

    def _acepta(self, token_type):
        # if there is next token and token type matches
        if self.next_token and self.next_token.type == token_type:
            self._avanza()
            return True
        else:
            return False

    def _espera(self, token_type):
        if not self._acepta(token_type):
            raise SyntaxError('Expected ' + token_type)

    def formula(self):
        '''
        formula : conjuncion | conjuncion ∨ formula
        '''
        formula_value = self.conjuncion()
        if self._acepta('OR'):
            formula_value = formula_value | self.formula()
        return formula_value

    def conjuncion(self):
        '''
        conjuncion : clausula | clausula ∧ conjuncion
        '''
        conj_value = self.clausula()
        if self._acepta('AND'):
            conj_value = conj_value & self.conjuncion()
        return conj_value

    def clausula(self):
        '''
        clausula : CONST | (formula)
        '''
        # Si aparece un parentesis

        if self._acepta('LPAREN'):
            formula_value = self.formula()
            self._espera('RPAREN')
            return formula_value
        elif self._acepta('CONST'):
            return self.asig[self.current_token.value]

    def satisfacible(self):

        asig_aux = self.asig.copy()

        for n in range(0, (len(asig_aux.keys()) ** 2)):
            m = n
            for v in asig_aux.keys():
                asig_aux[v] = bool(m % 2)
                m = m >> 1
                if self.prueba_asignacion(asig_aux):
                    return asig_aux
        return False

    def prueba_asignacion(self, asignacion):
        tmp = SentenciaBooleana()
        return tmp.parse(self.text, asignacion)

class GeneracionSentencias:
    def __init__(self, pos):
        self.pos = pos
        self.notp = False

    def sentencia(self):
        '''
        Sentencia retorna el string con la fórmula
        '''
        if self.pos % 2 == 0:
            self.pos = self.pos >> 1
            #randomly add negation
            if self.pos%2 == 1:
                self.notp=True
                self.pos = self.pos >> 1
                return '¬' + self.conjuncion()
            return self.conjuncion()
        else:
            self.pos = self.pos >> 1
            resultado = self.conjuncion()
            #randomly add negation
            if self.pos%2 == 1:
                self.notp=True
                self.pos = self.pos >> 1
                if self.pos%2 == 1:
                    self.notp=True
                    self.pos = self.pos >> 1
                    return '¬' + resultado + "∧" + self.sentencia()
                return resultado + "∨" + '¬' + self.sentencia()
            return resultado + "∨" + self.sentencia()


    def conjuncion(self):
        '''
        Sentencia retorna el string con la fórmula
        '''
        if self.pos%2 == 0:
            self.pos = self.pos >> 1
            #randomly add negation
            if self.pos%2 == 1:
                self.notp=True
                self.pos = self.pos >> 1
                return '¬' + self.clausula()
            return self.clausula()
        else:
            self.pos = self.pos >> 1
            resultado = self.clausula()
            #randomly add negation
            if self.pos%2 == 1:
                self.notp=True
                self.pos = self.pos >> 1
                if self.pos%2 == 1:
                    self.notp=True
                    self.pos = self.pos >> 1
                    return '¬' + resultado + "∧" + self.conjuncion()
                return resultado + "∧" + '¬' + self.conjuncion()
            return  resultado + "∧" + self.conjuncion()


    def clausula(self):
        '''
        Sentencia retorna el string con la fórmula
        '''
        if self.pos%2 == 0:
            self.pos = self.pos >> 1
            resultado, self.pos = chr(97 + (self.pos%25)), self.pos//25
            #randomly add negation
            if self.pos%2 == 1:
                self.notp=True
                self.pos = self.pos >> 1
                return '¬' + resultado
            return resultado
        else:
            self.pos = self.pos >> 1
            #randomly add negation
            if self.pos%2 == 1:
                self.notp=True
                self.pos = self.pos >> 1
                return '¬' + '(' + self.sentencia() + ')'
            return '(' + self.sentencia() + ')'





class SentenciaGeneral(SentenciaBooleana):

    def clausula(self):
        '''
            clausula : ¬ CONST | ¬ (sentencia)
        '''
        # si aparece un not
        if self._acepta('NOT'):
            return not super().clausula()
        # Si aparece un parentesis
        else:
            return super().clausula()


class sentenciaDot(SentenciaBooleana):
    '''
    Para generar el grafo, los nombres de los nodos seran un numero entero,
    y la etiqueta sera el simbolo correspondiente de la gramatica.

    Para generar los nodos sin que la recursividad suponga un problema, cada nodo (sentencia, clausula y conjuncion)
    conoceran su numero de nodo(se le pasa su nodo padre por parámetro) y se encargarán de dar un número de nodo a sus hijos,
    mientras se tiene un contador de nodos como atributo de la clase para que los nodos le vayan incrementando.

    De esta forma generaremos el arbol de derivacion en preorden(Primero el padre y despues los hijos, de izq a der)
    '''

    def __init__(self):
        self.g = graphviz.Digraph(comment='Arbol de derivacion')  # Grafo
        self.n = 0  # Contador de nodos
        self.g.node('0', 'Sentencia')  # Creamos la raiz

    def render(self):
        self.g.render('ArbolDerivacion.gv', view=True)

    def formula(self, nodo=0):
        '''
        formula : conjuncion | conjuncion ∨ formula
        '''
        self.n += 1

        self.g.node(str(self.n), 'Conjuncion')
        self.g.edge(str(nodo), str(self.n))

        formula_value = self.conjuncion(self.n)

        if self._acepta('OR'):
            self.g.node(str(self.n), 'OR')
            self.g.edge(str(nodo), str(self.n))
            self.n += 1

            self.g.node(str(self.n), 'Sentencia')
            self.g.edge(str(nodo), str(self.n))

            formula_value = formula_value | self.formula(self.n)
        return formula_value

    def conjuncion(self, nodo):
        '''
        conjuncion : clausula | clausula ∧ conjuncion
        '''
        self.n += 1
        self.g.node(str(self.n), 'Clausula')
        self.g.edge(str(nodo), str(self.n))

        conj_value = self.clausula(self.n)

        if self._acepta('AND'):
            self.g.node(str(self.n), 'AND')
            self.g.edge(str(nodo), str(self.n))

            self.n += 1

            self.g.node(str(self.n), 'Conjuncion')
            self.g.edge(str(nodo), str(self.n))
            conj_value = conj_value & self.conjuncion(self.n)
        return conj_value

    def clausula(self, nodo):
        '''
        clausula : CONST | (Formula)

        '''
        self.n += 1

        if self._acepta('NOT'):
            self.g.node(str(self.n), 'NOT')
            self.g.edge(str(nodo), str(self.n))
            self.n += 1
        # Si aparece un parentesis
        if self._acepta('LPAREN'):
            self.g.node(str(self.n), '(Sentencia)')
            self.g.edge(str(nodo), str(self.n))
            formula_value = self.formula(self.n)
            self.n += 1
            self._espera('RPAREN')
            return formula_value
        elif self._acepta('CONST'):
            self.g.node(str(self.n), self.current_token.value)
            self.g.edge(str(nodo), str(self.n))
            self.n += 1
            return self.asig[self.current_token.value]


if __name__ == '__main__':

    iters = 1000
    sentencias = []
    sentencias_not = []
    text = 'x ∨ ¬(y ∧ ¬y ∧ x)'
    asig = {'x': False, 'y': False}

    # Apartado 1

    e = SentenciaGeneral()
    print(e.parse(text, asig))

    # Apartado 2

    for i in range(iters):
        e = GeneracionSentencias(i)
        sentencias.insert(i,e.sentencia())
        if e.notp == True:
            sentencias_not.append([sentencias[i],i])

    print(sentencias)
    print(sentencias_not)

    # Apartado 3
    e = SentenciaBooleana()
    text_bool = 'x ∨ (y ∧ z ∧ x)'
    asig_bool = {'x': False, 'y': False, 'z': False}
    print(e.parse(text_bool, asig_bool))
    print(e.satisfacible())

    '''
    Explicacion del uso de la operacion % 25:

    Se utiliza para castear un número entero a una letra del abecedario. Se hace char chr(97 + (self.pos%25))
    donde 0x97 es el codigo ASCII de la primera letra del abecedario y 25 es el numero de letras que tienen el 
    abecedario ASCII. Por lo que se calcula para un numero la letra del abecedario que le corresponde
    '''

    # Apartado 4
    e = sentenciaDot()
    e.parse(text, asig)
    e.render()
    e.render()