import spacy
from spacy.matcher import Matcher
from spacy.tokens import Token
from spacy.tokens import Span
from spacy import displacy
from spacy.matcher import PhraseMatcher
from spacy.matcher import DependencyMatcher
from collections import deque

import logging


logger = logging.getLogger(__name__)

## temporary add stream handler
# ch = logging.StreamHandler()
# logger.addHandler(ch)
##




class RuleBasedMatcher(object):
  """
  """

  def __init__(self, nlp, *args, **kwargs):
    """
      Construct
      @ In, nlp, A spaCy language model object
      @ In, rules, str or list, where to read rules from
      @ In, args, list, positional arguments
      @ In, kwargs, dict, keyword arguments
      @ Out, None
    """
    self.type = self.__class__.__name__
    self.name = self.__class__.__name__
    logger.info(f'Create instance of {self.name}')
    # nlp = spacy.load("en_core_web_sm")
    # pipeline sequence: entity_ruler --> merge_entities --> coreferee
    self.nlp = nlp
    self._doc = None
    self._rules = {}
    self._match = False
    self._phraseMatch = False
    self._dependencyMatch = False
    self._entityRuler = False
    self.matcher = Matcher(nlp.vocab)
    self.phraseMatcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    self.dependencyMatcher = DependencyMatcher(nlp.vocab)
    self.entityRuler = nlp.add_pipe("entity_ruler")
    self._callbacks = {}
    self._asSpans = True # When True, a list of Span objects using the match_id as the span label will be returned
    self._matchedSents = [] # collect data of matched sentences to be visualized
    self._visualizeMatchedSents = True
    self._coref = False # True indicate coreference pipeline is available

    ## coreferee module for Coreference Resolution
    ## Q? at which level to perform coreferee? After NER and perform coreferee on collected sentence
    try:
      # check the current version spacy>=3.1.0,<3.2.0
      from packaging.version import Version
      ver = spacy.__version__
      valid = Version(ver)>=Version('3.1.0') and Version(ver)<Version('3.2.0')
      if valid:
        # https://github.com/msg-systems/coreferee
        import coreferee
        self._coref = True
        self.nlp.add_pipe('coreferee')
    except ModuleNotFoundError:
      logger.info('Module ')

  def addPattern(self, name, rules, callback=None):
    """
      Add rules
      @ In, name, str,
      @ In, rules, list,
        rules = [{"LOWER": "hello"}, {"IS_PUNCT": True}, {"LOWER": "world"}]
    """
    logger.debug('Add rules')
    if not isinstance(rules, list):
      rules = [rules]
    if not isinstance(rules[0], list):
      rules = [rules]
    self._rules[name] = rules
    self._callbacks[name] = callback
    self.matcher.add(name, rules, on_match=callback)
    if not self._match:
      self._match = True

  def addPhrase(self, name, phraseList, callback=None):
    """
      Add phrase patterns
      @ In, name, str,
      @ In, phraseList, list,
        phraseList = ["hello", "world"]
    """
    logger.debug(f'Add phrase pattern for {name}')
    patterns = [self.nlp.make_doc(text) for text in phraseList]
    self._callbacks[name] = callback
    self._rules[name] = patterns
    self.phraseMatcher.add(name, patterns, on_match=callback)
    if not self._phraseMatch:
      self._phraseMatch = True

  def addDependency(self, name, patternList, callback=None):
    """
      Add dependency pattern
      @ In, name, str,
      @ In, patternList, list,
    """
    logger.debug(f'Add dependency pattern for {name}')
    if not isinstance(patternList, list):
      patternList = [patternList]
    if not isinstance(patternList[0], list):
      patternList = [patternList]
    self._rules[name] = patternList
    self._callbacks[name] = callback
    self.dependencyMatcher.add(name, patternList, on_match=callback)
    if not self._dependencyMatch:
      self._dependencyMatch = True

  def addEntityPattern(self, name, patternList):
    """
      Add entity pattern, to extend doc.ents, similar function to self.extendEnt
      @ In, name, str,
      @ In, patternList, list, {"label": "GPE", "pattern": [{"LOWER": "san"}, {"LOWER": "francisco"}]}
    """
    if not self.nlp.has_pipe('entity_ruler'):
      self.nlp.add_pipe('entity_ruler')
    if not isinstance(patternList, list):
      patternList = [patternList]
    self.entityRuler.add_patterns(patternList)
    if not self._entityRuler:
      self._entityRuler = True

  def __call__(self, text):
    """
    """
    # Merging Entity Tokens
    # We need to consider how to do this, I sugguest to first conduct rule based NER, then collect
    # all related sentences, then create new pipelines to perform NER with "merge_entities" before the
    # conduction of relationship extraction
    # if self.nlp.has_pipe('merge_entities'):
    #   _ = self.nlp.remove_pipe('merge_entities')
    # self.nlp.add_pipe('merge_entities')

    doc = self.nlp(text)
    self._doc = doc
    matches = []
    if self._match:
      matches += self.matcher(doc, as_spans = self._asSpans) # <class 'list'>
    if self._phraseMatch:
      matches += self.phraseMatcher(doc, as_spans = self._asSpans) # <class 'list'>
    if self._dependencyMatch:
      depMatches = self.dependencyMatcher(doc) # <class 'list'> [tuple(match_id, token_ids)]

    if self._asSpans:
      for span in matches:
        logger.debug(f'Matches: {span.text}, {span.label_}')
    else:
      for id, start, end in matches:
        strID = self.nlp.vocab.strings[id]
        span = doc[start:end]
        logger.debug(f'Matches: {strID}, {start}, {end}, {span.text}')

    # print dependency matches
    for (id, tokenIDs) in depMatches:
      name = self.nlp.vocab.strings[id]
      for i in range(len(tokenIDs)):
        print(self._rules[name][0][i]["RIGHT_ID"] + ":",doc[tokenIDs[i]].text)

    ## use entity ruler to identify entity
    if self._entityRuler:
      print("Entity Ruler: \n",[(ent.text, ent.label_, ent.ent_id_) for ent in doc.ents])

    if self._coref:
      logger.debug('Print Coreference Info:')
      print(doc._.coref_chains.pretty_representation)


  def visualize():
    """
    """
    if self._visualizeMatchedSents:
      # Serve visualization of sentences containing match with displaCy
      # set manual=True to make displaCy render straight from a dictionary
      # (if you're not running the code within a Jupyer environment, you can
      # use displacy.serve instead)
      displacy.render(self._matchedSents, style="ent", manual=True)


  ##########################
  # methods for relation extraction
  ##########################

  def isPassive(self, token):
    """
    """
    if token.dep_.endswith('pass'): # noun
      return True
    for left in token.lefts: # verb
      if left.dep_ == 'auxpass':
        return True
    return False

  def bfs(self, root, entType, deps, firstDepOnly=False):
    """
      Return first child of root (included) that matches
      entType and dependency list by breadth first search.
      Search stops after first dependency match if firstDepOnly
      (used for subject search - do not "jump" over subjects)
    """
    toVisit = deque([root]) # queue for bfs

    while len(toVisit) > 0:
      child = toVisit.popleft()
      # print("child", child, child.dep_)
      if child.dep_ in deps:
        if child._.ref_t == entType:
          return child
        elif firstDepOnly: # first match (subjects)
          return None
      elif child.dep_ == 'compound' and \
         child.head.dep_ in deps and \
         child._.ref_t == entType: # check if contained in compound
        return child
      toVisit.extend(list(child.children))
    return None

  def findSubj(self, pred, entType, passive):
    """
      Find closest subject in predicates left subtree or
      predicates parent's left subtree (recursive).
      Has a filter on organizations.
    """
    for left in pred.lefts:
      if passive: # if pred is passive, search for passive subject
        subj = bfs(left, entType, ['nsubjpass', 'nsubj:pass'], True)
      else:
        subj = bfs(left, entType, ['nsubj'], True)
      if subj is not None: # found it!
        return subj
    if pred.head != pred and not self.isPassive(pred):
      return self.findSubj(pred.head, entType, passive) # climb up left subtree
    else:
      return None

  def findObj(self, pred, entType, exclPrepos):
    """
      Find closest object in predicates right subtree.
      Skip prepositional objects if the preposition is in exclude list.
      Has a filter on organizations.
    """
    for right in pred.rights:
      obj = bfs(right, entType, ['dobj', 'pobj', 'iobj', 'obj', 'obl'])
      if obj is not None:
        if obj.dep_ == 'pobj' and obj.head.lemma_.lower() in exclPrepos: # check preposition
          continue
        return obj
    return None

  def extractRelDep(doc, predName, predSynonyms, exclPrepos=[]):
    """
    """
    for token in doc:
      if token.pos_ == 'VERB' and token.lemma_ in predSynonyms:
        pred = token
        passive = self.isPassive(pred)
        subj = self.findSubj(pred, 'ORG', passive)
        if subj is not None:
          obj = self.findObj(pred, 'ORG', exclPrepos)
          if obj is not None:
            if passive: # switch roles
              obj, subj = subj, obj
            yield ((subj._.ref_n, subj._.ref_t), predName,
                   (obj._.ref_n, obj._.ref_t))

  ###############
  # methods can be used for callback in "add" method
  ###############
  def extendEnt(matcher, doc, i, matches):
    """
      Extend the doc's entity
      @ In, matcher, spacy.Matcher, the spacy matcher instance
      @ In, doc, the document the matcher was used on
      @ In, i, int, index of the current match (matches[i])
      @ In, matches, List[Tuple[int, int, int]], a list of (match_id, start, end) tuples, describing the matches. A
        match tuple describes a span doc[start:end]
    """
    id, start, end = matches[i]
    ent = Span(doc, start, end, label=id)
    doc.ents += (ent,)
    logger.debug(ent.text)

  def collectSents(matcher, doc, i, matches):
    """
      collect data of matched sentences that can be used for visualization
      @ In, matcher, spacy.Matcher, the spacy matcher instance
      @ In, doc, the document the matcher was used on
      @ In, i, int, index of the current match (matches[i])
      @ In, matches, List[Tuple[int, int, int]], a list of (match_id, start, end) tuples, describing the matches. A
        match tuple describes a span doc[start:end]
    """
    id, start, end = matches[i]
    span = doc[start:end]  # Matched span
    sent = span.sent  # Sentence containing matched span
    # Append mock entity for match in displaCy style to matched_sents
    # get the match span by ofsetting the start and end of the span with the
    # start and end of the sentence in the doc
    matchEnts = [{
        "start": span.start_char - sent.start_char,
        "end": span.end_char - sent.start_char,
        "label": "MATCH",
    }]
    self._matchedSents.append({"text": sent.text, "ents": matchEnts})
