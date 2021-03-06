#!/usr/bin/env python

# Copyright (C) 2006-2011  Open Data ("Open Data" refers to
# one or more of the following companies: Open Data Partners LLC,
# Open Data Research LLC, or Open Data Capital LLC.)
#
# This file is part of Augustus.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Define an XSD for the ProducerConsumer configuration file."""

from sys import version_info
if version_info < (2, 6): from sets import Set as set

# local includes
from augustus.core.xmlbase import load_xsdElement
from augustus.core.xmlbase import load_xsdGroup
from augustus.core.xmlbase import load_xsdType
from augustus.core.defs import Atom, NameSpace
import augustus.core.xmlbase as xmlbase

#################################################### ConfigurationError
class ConfigurationError(Exception): pass  # Any configuration error

# base class for all Config
class Config(xmlbase.XML):
    topTag = "AugustusConfiguration"
    xsdType = {}
    xsdGroup = {}
    classMap = {}

    def __init__(self, *children, **attrib):
        # reverse-lookup the classMap
        try:
            configName = (configName for configName, pythonObj in self.classMap.items() if pythonObj == self.__class__).next()
        except StopIteration:
            raise Exception, "Config class is missing from the classMap (programmer error)"
        xmlbase.XML.__init__(self, configName, *children, **attrib)

########################################################### Config types

Config.xsdType["LogSetup"] = load_xsdType("""
  <xs:complexType name="LogSetup">
    <xs:sequence>
      <xs:choice>
        <xs:element ref="ToLogFile"/>
        <xs:element ref="ToStandardError"/>
        <xs:element ref="ToStandardOut"/>
      </xs:choice>
    </xs:sequence>
    <xs:attribute name="level" use="optional">
      <!-- Note:
           For the root logger, level defaults to ERROR.
           For the metadata logger, level defaults to DEBUG.
           For the metadata logger, the only options are DEBUG,
           INFO, or no logging...
      -->
      <xs:simpleType>
        <xs:restriction base="xs:string">
          <xs:enumeration value="DEBUG"/>
          <xs:enumeration value="INFO"/>
          <xs:enumeration value="WARNING"/>
          <xs:enumeration value="ERROR"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:attribute>
    <xs:attribute
      name="formatString" type="xs:string"
      default="%(created)012.0f\t%(asctime)s\t%(levelname)s\t%(message)s"
      use="optional"/>
    <xs:attribute
      name="dateFmt" type="xs:string" default="%Y-%m-%dT%H:%M:%S"
      use="optional"/>
  </xs:complexType>
""")

Config.xsdType["WithTagAttributeType"] = load_xsdType("""
  <xs:complexType name="WithTagAttributeType">
    <xs:attribute name="name" type="xs:string" use="required"/>
  </xs:complexType>
""")

Config.xsdType["NullType"] = load_xsdType("""
  <xs:complexType name="NullType">
  </xs:complexType>
""")


######################################################## Config elements

class AugustusConfiguration(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="AugustusConfiguration">
    <xs:complexType>
      <xs:choice minOccurs="0" maxOccurs="unbounded">
        <xs:element ref="Logging"/>
        <xs:element ref="Metadata"/>
        <xs:element ref="AggregationSettings"/>
        <xs:element ref="EventSettings"/>
        <xs:element ref="ModelInput"/>
        <xs:element ref="DataInput"/>
        <xs:element ref="ConsumerBlending"/>
        <xs:element ref="Output"/>
        <xs:element ref="ModelSetup"/>
        <xs:element ref="ModelVerification"/>
      </xs:choice>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        """ Complain if neither producing nor consuming a model."""

        if not self.exists(ModelInput):
            raise xmlbase.XMLValidationError, "AugustusConfiguration must include a ModelInput"

        if not self.exists(DataInput):
            raise xmlbase.XMLValidationError, "AugustusConfiguration must include a DataInput"

        for element in ("Logging", "Metadata", "AggregationSettings", "EventSettings", "ModelInput",
                        "DataInput", "ConsumerBlending", "Output", "ModelSetup", "ModelVerification"):
            if len(self.matches(element)) > 1:
                raise xmlbase.XMLValidationError, "AugustusConfiguration may not include more than one %s" % element

        if self.exists(DataInput) and\
            not self.exists(ModelSetup) and\
            not self.exists(Output):

            raise xmlbase.XMLValidationError, " ".join([
                "If \"DataInput\" is set, and not producing a model,",
                "the \"Output\" must also be present to identify a",
                "file / location to write the output scores..."])

        if not self.exists(ModelSetup) and not self.exists(Output):
            raise xmlbase.XMLValidationError, " ".join([
                "At least one of \"Output\" or \"ModelSetup\"should be present,",
                "or else Augustus isn't going to make either a new model or any output scores..."])

Config.classMap["AugustusConfiguration"] = AugustusConfiguration

class Logging(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="Logging" type="LogSetup"/>
""")

Config.classMap["Logging"] = Logging

class Metadata(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="Metadata" type="LogSetup"/>
""")
    def post_validate(self):
        """ Restrict the logging levels to DEBUG or INFO."""
        if "level" in self.attrib:
            if self["level"] not in ("DEBUG", "INFO"):
                raise xmlbase.XMLValidationError, " ".join([
                    "The only two allowed logging levels for Metadata ",
                    "are 'DEBUG' and 'INFO'"])

Config.classMap["Metadata"] = Metadata

class FileRotateBySize(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="FileRotateBySize">
    <xs:complexType>
      <xs:attribute name="mode" default="a" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="a"/>
            <xs:enumeration value="w"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute
        name="maxBytes" default="0" type="xs:integer" use="optional"/>
      <xs:attribute
        name="backupCount" default="0" type="xs:integer" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["FileRotateBySize"] = FileRotateBySize

class FileRotateByTime(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="FileRotateByTime">
    <xs:complexType>
      <xs:attribute name="when" default="H" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="H"/><!-- Hours -->
            <xs:enumeration value="D"/><!-- Days -->
            <xs:enumeration value="midnight"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute
        name="interval" default="1" type="xs:integer" use="optional"/>
      <xs:attribute
        name="backupCount" default="0" type="xs:integer" use="optional"/>
      <xs:attribute
        name="utc" default="0" type="xs:boolean" use="optional"/>
        <!-- if true, use local time, otherwise use UTC -->
    </xs:complexType>
  </xs:element>
""")

Config.classMap["FileRotateByTime"] = FileRotateByTime

class ModelInput(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ModelInput">
    <xs:complexType>
      <xs:choice>
        <xs:element ref="FromFile"/>
        <xs:element ref="FromFifo"/>
      </xs:choice>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["ModelInput"] = ModelInput

class DataInput(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="DataInput">
    <!-- DataInput is ignored if the ProducerConsumer
      is instructed to only create a model. Then the training
      data referenced in the model build instructions are used. -->
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="ReadOnce" minOccurs="0"/>
        <!-- only include "ReadOnce" if reading from one of:
                * a CSV file
                * a file containing a UniTable data structure
             or if performing event-based scoring -->
        <xs:choice>
          <xs:element ref="Interactive"/>
          <xs:element ref="FromCSVFile"/>
          <xs:element ref="FromFile"/>
          <xs:element ref="FromFifo"/>
          <xs:element ref="FromFixedRecordFile"/>
          <xs:element ref="FromHTTP"/>
          <xs:element ref="FromStandardIn"/>
        </xs:choice>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        """ If ReadOnce is present make sure we are not reading
            from a Fifo or an HTTP.  Also, if reading from a Fifo
            and ReadOnce is present, require a header string.
        """
        if "selectmode" in self.attrib:
            raise xmlbase.XMLValidationError, " ".join([
                "\"selectmode\" is not an available attribute option",
                "for \"DataInput\".  If a glob is used in the \"name\"",
                "attribute of \"DataInput\", all files will be read in",
                "alphabetical order."])
        if self.matches(ReadOnce) and self.matches(FromHTTP):
            raise xmlbase.XMLValidationError, " ".join([
                "Cannot use the \"ReadOnce\" to read from an HTTP server"])
#        if not self.matches(ReadOnce) and self.matches(FromFifo):
#            if not "header" in self.child(FromFifo).attrib:
#                raise xmlbase.XMLValidationError, " ".join([
#                    "Must have a separate 'header' when reading",
#                    "forever from a named file pipe (FromFifo)...and",
#                    "user will have to strip the header from each of",
#                    "these files."])


Config.classMap["DataInput"] = DataInput

class ReadOnce(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ReadOnce" type="NullType"/>
""")

Config.classMap["ReadOnce"] = ReadOnce

class AggregationSettings(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="AggregationSettings">
    <xs:complexType>
      <xs:attribute name="score" type="xs:boolean" use="optional"/>
      <xs:attribute name="output" type="xs:boolean" use="optional"/>
      <xs:attribute name="atEnd" type="xs:boolean" default="true" use="optional"/>
      <xs:attribute name="eventNumberInterval" type="xs:integer" default="-1" use="optional"/>
      <xs:attribute name="fieldValueInterval" type="xs:integer" default="-1" use="optional"/>
      <xs:attribute name="field" type="xs:string" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        self.attrib["score"] = self.attrib.get("score", False)
        self.attrib["output"] = self.attrib.get("output", False)

        if "atEnd" not in self.attrib:
            self["atEnd"] = True

        if "eventNumberInterval" not in self.attrib:
            self["eventNumberInterval"] = -1

        if "fieldValueInterval" not in self.attrib:
            self["fieldValueInterval"] = -1

        if self["fieldValueInterval"] >= 0:
            if "field" not in self.attrib:
                raise XMLValidationError, "If \"fieldValueInterval\" is non-negative, then the \"field\" must be specified."

Config.classMap["AggregationSettings"] = AggregationSettings


class EventSettings(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="EventSettings">
    <xs:complexType>
      <xs:attribute name="score" type="xs:boolean" use="optional"/>
      <xs:attribute name="output" type="xs:boolean" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        self.attrib["score"] = self.attrib.get("score", False)
        self.attrib["output"] = self.attrib.get("output", False)

Config.classMap["EventSettings"] = EventSettings


class Output(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="Output">
    <xs:complexType>
      <xs:sequence>
        <xs:choice>
          <xs:element ref="ToFile"/>
          <xs:element ref="ToHTTP"/>
          <xs:element ref="ToStandardError"/>
          <xs:element ref="ToStandardOut"/>
        </xs:choice>
        <xs:element ref="ReportTag" minOccurs="0"/>
        <xs:element ref="EventTag" minOccurs="0"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["Output"] = Output

class Interactive(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="Interactive" type="NullType"/>
""")

Config.classMap["Interactive"] = Interactive

class ReportTag(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ReportTag">
    <xs:complexType>
      <xs:attribute name="name" type="xs:string" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["ReportTag"] = ReportTag

class ModelSetup(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ModelSetup">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="Serialization" minOccurs="0"/>
        <xs:element ref="ProducerBlending" minOccurs="0"/>
        <xs:element ref="ZeroVarianceHandling" minOccurs="0"/>
        <!-- if omitted, the default will be to use
             ZeroVarianceHandling with method="exception" -->
        <xs:element ref="SegmentationSchema" minOccurs="0"/>
      </xs:sequence>
      <xs:attribute name="outputFilename" type="xs:string" use="optional"/>
      <xs:attribute name="mode" use="optional" default="replaceExisting">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="lockExisting"/>
            <xs:enumeration value="replaceExisting"/>
            <!-- replace: create statistics from just the new data  -->
            <xs:enumeration value="updateExisting"/>
            <!-- update: modify statistics with the new data  -->
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute name="updateEvery" use="optional" default="event">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="event"/>
            <xs:enumeration value="aggregate"/>
            <xs:enumeration value="both"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        if self.exists(ZeroVarianceHandling):
            raise NotImplementedError, " ".join([
                "Zero variance handling options are not yet implemented"])

        if "mode" in self.attrib and self["mode"]=="lockExisting":
            if not self.exists(ProducerBlending, maxdepth=1):
                if not self.exists(SegmentationSchema, maxdepth=1):
                    raise xmlbase.XMLValidationError, " ".join([
                        "Model 'mode' is 'lockExisting', but there are no",
                        "new segments defined and a 'ProducerBlending'",
                        "configuration exists; nothing is going to",
                        "change in the model at all...\nPlease omit",
                        "the entire \"ModelSetup\" element if you",
                        "want this behavior, or else add segmentation",
                        "or modify the \"ModelSetup\" 'mode' attribute."])


Config.classMap["ModelSetup"] = ModelSetup

class Serialization(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="Serialization">
    <xs:complexType>
      <xs:attribute
        name="writeFrequency" type="xs:integer" use="optional"/>
        <xs:attribute name="frequencyUnits" use="optional">
          <xs:simpleType>
            <xs:restriction base="xs:string">
              <xs:enumeration value="M"/>
              <xs:enumeration value="H"/>
              <xs:enumeration value="d"/>
              <xs:enumeration value="observations"/>
            </xs:restriction>
          </xs:simpleType>
        </xs:attribute>
      <xs:attribute name="storage" default="asPMML" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="asPickle"/>
            <xs:enumeration value="asPMML"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        if "writeFrequency" in self.attrib:
            if not "frequencyUnits" in self.attrib:
                raise xmlbase.XMLValidationError, " ".join([
                    "\"writeFrequency\" and \"frequencyUnits\" must be",
                    "both be present together"])
        elif "frequencyUnits" in self.attrib:
            raise xmlbase.XMLValidationError, " ".join([
                "\"writeFrequency\" and \"frequencyUnits\" must be",
                "both be present together"])

Config.classMap["Serialization"] = Serialization

class ProducerBlending(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ProducerBlending">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="MaturityThreshold" minOccurs="0"/>
      </xs:sequence>
      <xs:attribute name="method" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="computerTimeWindowSeconds"/>
            <xs:enumeration value="eventTimeWindow"/>
            <xs:enumeration value="exponential"/>
            <xs:enumeration value="unweighted"/>
            <xs:enumeration value="window"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute name="alpha" type="xs:double" use="optional"/>
      <xs:attribute name="timeFieldName" type="xs:string" use="optional"/>
      <xs:attribute name="windowLag" type="xs:integer" use="optional"/>
      <xs:attribute name="windowSize" type="xs:integer" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        # FIXME: some of these attributes, like "timeFieldName", are
        # always optional, which breaks the logic of this check

        need_template = "Need \"%s\" with %s blending"
        no_template = "No \"%s\" attribute allowed when using \"%s\""

        needs = {}
        needs["computerTimeWindowSeconds"] = set(["windowSize"])
        needs["eventTimeWindow"] = set(["windowSize"])
        needs["exponential"] = set(["alpha"])
        needs["unweighted"] = set()
        needs["window"] = set(["windowSize"])
        options = set(self.attrib)
        if "method" in self.attrib:
            options.remove("method")
            method = self["method"]
        else:
             method = "unweighted"
        for need in needs[method] - options:
            raise xmlbase.XMLValidationError, need_template % (need, method)
        if "windowLag" in options and method not in ("unweighted", "exponential"):
            options.remove("windowLag")
        for no in options - needs[method]:
            if no != "timeFieldName":
                raise xmlbase.XMLValidationError, no_template % (no, method)

Config.classMap["ProducerBlending"] = ProducerBlending

class ConsumerBlending(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ConsumerBlending">
    <xs:complexType>
      <xs:attribute name="method" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="computerTimeWindowSeconds"/>
            <xs:enumeration value="eventTimeWindow"/>
            <xs:enumeration value="exponential"/>
            <xs:enumeration value="unweighted"/>
            <xs:enumeration value="window"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute name="alpha" type="xs:double" use="optional"/>
      <xs:attribute name="timeFieldName" type="xs:string" use="optional"/>
      <xs:attribute name="windowLag" type="xs:integer" use="optional"/>
      <xs:attribute name="windowSize" type="xs:integer" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        # FIXME: some of these attributes, like "timeFieldName", are
        # always optional, which breaks the logic of this check

        need_template = "Need \"%s\" with %s blending"
        no_template = "No \"%s\" attribute allowed when using \"%s\""

        needs = {}
        needs["computerTimeWindowSeconds"] = set(["windowSize"])
        needs["eventTimeWindow"] = set(["timeFieldName", "windowSize"])
        needs["exponential"] = set(["alpha"])
        needs["unweighted"] = set()
        needs["window"] = set(["windowSize"])
        options = set(self.attrib)
        if "method" in self.attrib:
            options.remove("method")
            method = self["method"]
        else:
             method = "unweighted"
        for need in needs[method] - options:
            raise xmlbase.XMLValidationError, need_template % (need, method)
        if "windowLag" in options and method not in ("unweighted", "exponential"):
            options.remove("windowLag")
        for no in options - needs[method]:
            if no != "timeFieldName":
                raise xmlbase.XMLValidationError, no_template % (no, method)

Config.classMap["ConsumerBlending"] = ConsumerBlending

class MaturityThreshold(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="MaturityThreshold">
    <xs:complexType>
      <xs:attribute name="threshold" type="xs:integer" use="required"/>
      <xs:attribute name="lockingThreshold" type="xs:integer" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["MaturityThreshold"] = MaturityThreshold

class ZeroVarianceHandling(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ZeroVarianceHandling">
    <xs:complexType>
      <xs:attribute name="method" default="exception" use="optional">
        <xs:simpleType>
        <xs:restriction base="xs:string">
          <xs:enumeration value="exception"/>
          <xs:enumeration value="quiet"/>
          <xs:enumeration value="varianceDefault"/>
          <xs:enumeration value="interpolateZeroVarianceEstimate"/>
        </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute
        name="value" type="xs:double" use="optional"/>
        <!-- only use "value" with method="VarianceDefault";
        it sets the default variance -->
      <xs:attribute
        name="resolution" type="xs:double" use="optional"/>
        <!-- only use "resolution" with
        method="InterpolateZeroVarianceEstimate";
        it sets the initial variance, to be shrunk with data
        size, by presuming the reason zero variance was
        observed was because the resolution of the data
        (e.g. integers) was bigger than the variance
        (which, say, equals 0.5) -->
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        if "value" in self.attrib:
            if "method" in self.attrib and not self["method"]=="varianceDefault":
                    raise xmlbase.XMLValidationError, "Can only use \"value\" with \"varianceDefault\""
        if "resolution" in self.attrib:
            if "method" in self.attrib and not self["method"]=="interpolateZeroVarianceEstimate":
                    raise xmlbase.XMLValidationError, "Can only use \"resolution\" with \"interpolateZeroVarianceEstimate\""

Config.classMap["ZeroVarianceHandling"] = ZeroVarianceHandling

class SegmentationSchema(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="SegmentationSchema">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="BlacklistedSegments" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element ref="SpecificSegments" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element ref="GenericSegment" minOccurs="0"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
""")

    def _everCollides(self, itemsA, rangesA, itemsB, rangesB):
        if len(itemsA.intersection(itemsB)) > 0:
            return True
        else:
            for item in itemsA:
                item = float(item)
                for rng in rangesB:
                    low = rng[0]
                    high = rng[1]
                    closure = rng[2]
                    if low < item and item < high:
                        return True
                    elif low == item and closure.startswith('c'):
                        return True
                    elif high == item and closure.beginswith('d'):
                        return True
            for item in itemsB:
                item = float(item)
                for rng in rangesA:
                    low = rng[0]
                    high = rng[1]
                    closure = rng[2]
                    if low < item and item < high:
                        return True
                    elif low == item and closure.startswith('c'):
                        return True
                    elif high == item and closure.beginswith('d'):
                        return True
        return False


    def post_validate(self):
        """Check that there are no collisions in the list of SpecificSegments."""
        # A collision exists if any of the SpecificSegments's set of fields
        # can be totally exhausted before or at the same time as any other
        # SpecificSegment's set of fields.
        self.whiteList = None
        self.blackList = None
        self.generic = None
        specifics = self.matches(SpecificSegments, maxdepth=1)
        N = len(specifics)
        for i in xrange(N):
            current = specifics[i].fields
            for j in xrange(N):
                if i != j:
                    compare = specifics[j].fields
                    def anyCollide(field, y):
                        return self._everCollides(current[field].items, current[field].ranges, compare[field].items, compare[field].ranges) and y

                    keysIntersection = set(current.keys()) & set(compare.keys())
                    collides = reduce(anyCollide, keysIntersection, False)
                    if collides:
                        # If along every dimension in the intersection
                        # there is a collision, the segments collide.
                        raise xmlbase.XMLValidationError, " ".join([
                            "Segments described in different",
                            "\"SpecificSegments\" sections overlap."])

        if N > 0:
            self.whiteList = [item.fields for item in specifics]
        blackListed = self.matches(BlacklistedSegments, maxdepth=1)
        if blackListed:
            self.blackList = [item.fields for item in blackListed]
        generic = self.child(GenericSegment, exception=False)
        if generic:
            self.generic = [generic.fields]

Config.classMap["SegmentationSchema"] = SegmentationSchema

class ToLogFile(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ToLogFile">
    <xs:complexType>
      <xs:sequence>
        <xs:choice minOccurs="0">
          <xs:element ref="FileRotateBySize"/>
          <xs:element ref="FileRotateByTime"/>
        </xs:choice>
      </xs:sequence>
      <xs:attribute name="name" type="xs:string" use="required"/>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["ToLogFile"] = ToLogFile

class ToFile(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ToFile">
    <xs:complexType>
      <xs:attribute name="name" type="xs:string" use="required"/>
      <xs:attribute name="type" default="XML" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="JSON"/>
            <xs:enumeration value="XML"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute name="overwrite" type="xs:boolean" default="false" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        outputType = self.attrib.get("type", "XML")
        if outputType == "JSON":
            raise NotImplementedError, \
                "The \"JSON\" output format is not yet implemented"

Config.classMap["ToFile"] = ToFile

class ToHTTP(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ToHTTP">
    <xs:complexType>
      <xs:attribute name="host" type="xs:string" use="required"/>
      <xs:attribute name="port" type="xs:string" use="optional"/>
      <xs:attribute name="url" type="xs:anyURI" use="required"/>
      <xs:attribute name="type" default="XML" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="JSON"/>
            <xs:enumeration value="XML"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["ToHTTP"] = ToHTTP

class ToStandardError(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ToStandardError">
    <xs:complexType>
      <xs:attribute name="type" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="JSON"/>
            <xs:enumeration value="XML"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["ToStandardError"] = ToStandardError

class ToStandardOut(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ToStandardOut">
    <xs:complexType>
      <xs:attribute name="type" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="JSON"/>
            <xs:enumeration value="XML"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["ToStandardOut"] = ToStandardOut

class FromCSVFile(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="FromCSVFile">
    <xs:complexType>
      <xs:attribute name="name" type="xs:string" use="required"/>
      <xs:attribute name="header" type="xs:string" use="optional"/>
      <xs:attribute name="sep" type="xs:string" use="optional"/>
      <xs:attribute name="framing" type="xs:string" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["FromCSVFile"] = FromCSVFile

class FromFifo(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="FromFifo">
    <xs:complexType>
      <xs:attribute name="type" default="XML" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="CSV"/>
            <xs:enumeration value="UniTable"/>
            <xs:enumeration value="XML"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute name="name" type="xs:string" use="required"/>
      <xs:attribute name="header" type="xs:string" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        if "type" not in self.attrib or self["type"]=="XML":
            if "header" in self.attrib:
                raise xmlbase.XMLValidationError,\
                    "An XML file is incompatible with a CSV header string"

Config.classMap["FromFifo"] = FromFifo

class FromFile(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="FromFile">
    <xs:complexType>
      <xs:attribute name="type" default="XML" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="CSV"/>
            <xs:enumeration value="UniTable"/>
            <xs:enumeration value="XML"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute name="name" type="xs:string" use="required"/>
      <xs:attribute name="selectmode" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="lastAlphabetic"/>
            <xs:enumeration value="mostRecent"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["FromFile"] = FromFile

class FromFixedRecordFile(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="FromFixedRecordFile">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="RecordField" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="name" type="xs:string" use="required"/>
      <xs:attribute name="cr" type="xs:string" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["FromFixedRecordFile"] = FromFixedRecordFile

class RecordField(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="RecordField">
    <xs:complexType>
      <xs:attribute name="name" type="xs:string" use="required"/>
      <xs:attribute name="length" type="xs:integer" use="required"/>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["RecordField"] = RecordField

class FromHTTP(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="FromHTTP">
    <xs:complexType>
      <xs:attribute name="url" type="xs:anyURI" use="required"/>
      <xs:attribute name="port" type="xs:string" use="required"/>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["FromHTTP"] = FromHTTP

class FromStandardIn(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="FromStandardIn" type="NullType"/>
""")

Config.classMap["FromStandardIn"] = FromStandardIn

class EventTag(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="EventTag">
    <xs:complexType>
      <xs:attribute name="name" type="xs:string" 
        default="Event" use="optional"/>
      <xs:attribute name="pseudoName" type="xs:string"
        default="pseudoEvent" use="optional"/>
   </xs:complexType>
  </xs:element>
""")

Config.classMap["EventTag"] = EventTag

class AllSegments:
    """Subclassed by SpecificSegments, BlacklistedSegments, GenericSegment.

    Provides methods to check whether new additions collide with
    existing entries to the segment definitions, and to find a match
    """
    class Inf(Atom):
        def __gt__(self, other): return True
        def __ge__(self, other): return True
        def __lt__(self, other): return False
        def __le__(self, other): return other is self or False
    INF = Inf("Inf")

    class NegInf(Atom):
        def __gt__(self, other): return False
        def __ge__(self, other): return other is self or False
        def __lt__(self, other): return True
        def __le__(self, other): return True
    NEGINF = NegInf("NegInf")


    def _addItems(self, field, include_items, exclude_items):
        if not hasattr(self, "fields"):
            self.fields = {}
        if field not in self.fields:
            self.fields[field] = NameSpace(
                include_items=include_items,
                exclude_items=exclude_items,
                ranges=[],
                partitions=[])
        else:
            self._checkItemsCollision(field, include_items)
            self.fields[field].include_items.update(include_items)
            self.fields[field].exclude_items.extend(exclude_items)

    def _addRanges(self, field, ranges):
        if not hasattr(self, "fields"):
            self.fields = {}
        if field not in self.fields:
            self.fields[field] = NameSpace(include_items=set(), exclude_items=[], ranges=ranges, partitions=[])
        else:
            self._checkRangesCollision(field, ranges)
            self.fields[field].ranges.extend(ranges)
            self.fields[field].ranges.sort()

    def _checkItemsCollision(self, field, include_items):
        if self.fields[field].include_items == None or include_items == None:
                raise xmlbase.XMLValidationError, " ".join([
                    "An \"EnumeratedDimension\" for field %s exists with no \"Selection\" identified, which is interpreted as a" % field,
                    "command to auto-generate segments for that field. No further specification can be made for that field"])
        partitions = self.fields[field].partitions

    def _checkRangesCollision(self, field, ranges):
        if self.fields[field].include_items == None:
            raise xmlbase.XMLValidationError, " ".join([
                "An \"EnumeratedDimension\" for field %s exists with no \"Selection\" identified, which is interpreted as a" % field,
                "command to auto-generate segments for that field. No further specification can be made for that field"])

    def _createPartitions(self):
        for key, field in self.fields.iteritems():
            field.ranges.sort
            field.partitions = []
            lookupStart = 0
            for i, (left, right, closure, divisions) in enumerate(field.ranges):
                if left is AllSegments.NEGINF or right is AllSegments.INF:
                    field.partitions.append((left, right, closure))
                else:
                    step = (right - left) / divisions
                    finish = divisions - 1
                    field.partitions.extend([(
                        j * step + left,
                        (j+1) * step + left if not j == finish else right,
                        closure)
                        for j in range(divisions)])

                newTuple = (left, right, closure, divisions, lookupStart)
                field.ranges[i] = newTuple
                lookupStart += divisions


class SpecificSegments(Config, AllSegments):
    xsd = load_xsdElement(Config, """
  <xs:element name="SpecificSegments">
    <xs:complexType>
      <xs:sequence>
        <xs:element
          ref="EnumeratedDimension" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element
          ref="PartitionedDimension" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        for element in self.matches(EnumeratedDimension):
            if len(element.children) == 0:
                raise xmlbase.XMLValidationError, "Must specify a selection for \"EnumeratedDimension\" in \"SpecificSegments\""
            self._addItems(element["field"], element.include_items, element.exclude_items)
        for element in self.matches(PartitionedDimension):
            self._addRanges(element["field"], element.ranges)
        self._createPartitions()

Config.classMap["SpecificSegments"] = SpecificSegments

class BlacklistedSegments(Config, AllSegments):
    xsd = load_xsdElement(Config, """
  <xs:element name="BlacklistedSegments">
    <xs:complexType>
      <xs:sequence>
        <xs:element
          ref="EnumeratedDimension" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element
          ref="PartitionedDimension" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        for element in self.matches(EnumeratedDimension):
            if len(element.children)==0:
                raise xmlbase.XMLValidationError, " ".join([
                    "Must specify a selection for \"EnumeratedDimension\" in \"BlacklistedSegments\""])
            self._addItems(element["field"], element.include_items, element.exclude_items)
        for element in self.matches(PartitionedDimension):
            self._addRanges(element["field"], element.ranges)
        self._createPartitions()

Config.classMap["BlacklistedSegments"] = BlacklistedSegments

class GenericSegment(Config, AllSegments):
    xsd = load_xsdElement(Config, """
  <xs:element name="GenericSegment">
    <xs:complexType>
      <xs:sequence>
        <xs:element
          ref="EnumeratedDimension" minOccurs="0" maxOccurs="unbounded"/>
        <xs:element
          ref="PartitionedDimension" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        emptyDimensions = 0
        for element in self.matches(EnumeratedDimension):
            if len(element.matches(Selection)) == 0:
                emptyDimensions += 1
            self._addItems(element["field"], element.include_items, element.exclude_items)

        if emptyDimensions == 0:
            raise xmlbase.XMLValidationError, "Must have at least one \"EnumeratedDimension\" section empty when in \"GenericSegment\""
        for element in self.matches(PartitionedDimension):
            self._addRanges(element["field"], element.ranges)
        self._createPartitions()

Config.classMap["GenericSegment"] = GenericSegment

class EnumeratedDimension(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="EnumeratedDimension">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="Selection" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="field" type="xs:string" use="required"/>
    </xs:complexType>
  </xs:element>
""")

    def post_validate(self):
        includeList = self.matches(lambda x: isinstance(x, Selection) and x.attrib.get("operator","equal") == "equal")
        if len(includeList):
            self.include_items = set([selection.attrib['value'] for selection in includeList])
        else:
            self.include_items = None

        excludeList = self.matches(lambda x: isinstance(x, Selection) and x.attrib.get("operator","equal") == "notEqual")
        self.exclude_items = [selection.attrib['value'] for selection in excludeList]

Config.classMap["EnumeratedDimension"] = EnumeratedDimension

class Selection(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="Selection">
    <xs:complexType>
      <xs:attribute name="value" type="xs:string" use="required"/>
      <xs:attribute name="operator" default="equal" use="optional">
      <!-- if 'operator' is notEqual, only one Selection can exist. -->
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="equal"/>
            <xs:enumeration value="notEqual"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["Selection"] = Selection

class PartitionedDimension(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="PartitionedDimension">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="Partition" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:attribute name="field" type="xs:string" use="required"/>
    </xs:complexType>
  </xs:element>
""")

    def _addRangeTuple(self, partition):
        bLow = partition._getWithDefault('low', AllSegments.NEGINF)
        bHigh =  partition._getWithDefault('high', AllSegments.INF)
        bClosure =  partition._getWithDefault('closure', 'openClosed')
        bDivisions =  partition._getWithDefault('divisions', 1)
        for aLow, aHigh, aClosure, x in self.ranges:
            # check if the beginning of new is in any of the old items
            try:
                if (aLow < bLow and bLow < aHigh) or\
                    (bLow < aLow and aLow < bHigh):
                    # (abab, abba) or (baba, baab)
                    raise xmlbase.XMLValidationError
                if aHigh == bLow and\
                    aClosure.endswith('d') and bClosure.startswith('c'):
                    # aa][bb
                    raise xmlbase.XMLValidationError
                if bHigh == aLow and\
                    bClosure.endswith('d') and aClosure.startswith('c'):
                    # bb][aa
                    raise xmlbase.XMLValidationError
            except xmlbase.XMLValidationError:
                raise xmlbase.XMLValidationError, " ".join([
                    "Collision in \"PartitionedDimension\": the partition with low, high values of",
                    "%s, %s overlaps another partition's range" % (str(bLow), str(bHigh)) ])
        self.ranges.append((bLow, bHigh, bClosure, bDivisions))

    def post_validate(self):
        definitionList = self.matches(Partition)
        if len(definitionList) == 0:
            raise xmlbase.XMLValidationError, "Must specify at least one partition in \"PartitionedDimension\""
        self.ranges = []
        for definition in definitionList:
            self._addRangeTuple(definition)

Config.classMap["PartitionedDimension"] = PartitionedDimension

class Partition(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="Partition">
    <xs:complexType>
      <xs:attribute name="low" type="xs:double" use="optional"/>
      <xs:attribute name="high" type="xs:double" use="optional"/>
      <xs:attribute name="divisions" type="xs:integer" use="optional"/>
      <!-- if 'divisions is present:
         * Closure cannot be closedClosed
         * Closure cannot be openOpen
         * both 'low' and 'high' must be present. -->
      <xs:attribute name="closure" default="openClosed" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="closedClosed"/>
            <xs:enumeration value="closedOpen"/>
            <xs:enumeration value="openClosed"/>
            <xs:enumeration value="openOpen"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
    </xs:complexType>
  </xs:element>
""")

    def _getWithDefault(self, key, default):
        tmp = default if key not in self.attrib else self[key]
        if tmp not in (AllSegments.NEGINF, AllSegments.INF):
            try:
                if key in ('low', 'high'):
                    tmp = float(tmp)
                if key == 'divisions':
                    tmp = int(tmp)
            except ValueError:
                raise xmlbase.XMLValidationError, " ".join([
                    "In \"Partition\", the low and high values",
                    "must be convertible to floats (or absent), and the",
                    "divisions must be convertible to an integer"])
        return tmp

    def post_validate(self):
        if 'low' in self.attrib and 'high' in self.attrib and\
            self['low'] > self['high']:

            raise xmlbase.XMLValidationError, " ".join([
                "'low' value in \"Partition\" must be less than",
                "'high' value in \"Partition\""])

        if 'divisions' in self.attrib:
            if 'divisions' <= 0:
                raise xmlbase.XMLValidationError, " ".join([
                    "'divisions' in \"Partition\" must be one or greater"])
            if 'divisions' > 1:
                if 'low' not in self.attrib or 'high' not in self.attrib:
                    raise xmlbase.XMLValidationError, " ".join([
                        "A \"Partition\" with 'divisions' must have",
                        "both the 'low' and 'high' bound defined"])
                if 'closure' in self.attrib and\
                    self['closure'] in ('closedClosed', 'openOpen'):

                    raise xmlbase.XMLValidationError, " ".join([
                        "A \"Partition\" with 'divisions' cannot",
                        "use 'closure' values of 'closedClosed'",
                        "(ranges would overlap) or 'openOpen'",
                        "(ranges would exclude their boundary)"])
        else:
            if 'low' not in self.attrib and 'closure' in self.attrib:
                if self['closure'].startswith('c'):
                    raise xmlbase.XMLValidationError, " ".join([
                        "A \"Partition\" that is unbounded on the",
                        "low end cannot use 'closure' values of",
                        "'closedClosed' or 'closedOpen'"])
            if 'high' not in self.attrib:
                if 'closure' not in self.attrib:
                    raise xmlbase.XMLValidationError, " ".join([
                        "A \"Partition\" that is unbounded on the",
                        "high end cannot use 'closure' values of",
                        "'openClosed', which is the default..."])
                elif self['closure'].endswith('d'):
                    raise xmlbase.XMLValidationError, " ".join([
                        "A \"Partition\" that is unbounded on the",
                        "high end cannot use 'closure' values of",
                        "'closedClosed' or 'openClosed'"])

Config.classMap["Partition"] = Partition

class AlternateDistribution(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="AlternateDistribution">
    <xs:complexType>
      <xs:choice>
        <xs:element ref="Distribution"/>
        <xs:element ref="MeanShift"/>
      </xs:choice>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["AlternateDistribution"] = AlternateDistribution

class MeanShift(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="MeanShift">
    <xs:complexType>
      <xs:attribute name="sigmas" type="xs:double" use="required"/>
      <!-- alternate distribution is the baseline with mean
           multiplied by "sigmas" -->
    </xs:complexType>
  </xs:element>
""")

Config.classMap["MeanShift"] = MeanShift

class Distribution(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="Distribution">
    <xs:complexType>
      <xs:attribute name="dist" use="required">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="gaussian"/>
            <xs:enumeration value="poisson"/>
            <xs:enumeration value="exponential"/>
            <xs:enumeration value="uniform"/>
            <xs:enumeration value="discrete"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute name="file" type="xs:string" use="required"/>
      <xs:attribute name="type" default="XML" use="optional">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="CSV"/>
            <xs:enumeration value="UniTable"/>
            <xs:enumeration value="XML"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute name="header" type="xs:string" use="optional"/>
      <xs:attribute name="sep" type="xs:string" use="optional"/>
      <xs:attribute name="types" type="xs:string" use="optional"/>
    </xs:complexType>
  </xs:element>
""")

Config.classMap["Distribution"] = Distribution

class ModelVerification(Config):
    xsd = load_xsdElement(Config, """
  <xs:element name="ModelVerification">
    <xs:complexType>
      <xs:attribute name="checkModel" type="xs:boolean" default="true" use="optional" />
      <xs:attribute name="checkSegments" type="xs:boolean" default="true" use="optional" />
      <xs:attribute name="onFailures" default="halt">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="halt"/>
            <xs:enumeration value="report"/>
          </xs:restriction>
        </xs:simpleType>
      </xs:attribute>
      <xs:attribute name="reportInScores" type="xs:boolean" default="false" use="optional" />
    </xs:complexType>
  </xs:element>
""")

Config.classMap["ModelVerification"] = ModelVerification
