# -*- coding: utf-8 -*-

"""Style configuration service for inline report presentation tokens.

This service loads the centralized JSON style config, applies safe defaults,
validates the minimum required shape, and builds render-ready inline CSS
variables plus inline ECharts theme context.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


DEFAULT_REPORT_STYLE: dict[str, Any] = {'meta': {'name': 'default',
          'version': '1.0.0',
          'description': 'Central presentation tokens for the current report system. Applies to both daily '
                         'and periodic families through inline CSS / inline chart theme generation.'},
 'font': {'family': 'Arial, Helvetica, sans-serif',
          'sizeBase': '12px',
          'sizeSmall': '11px',
          'sizeLarge': '13px',
          'sizeTitle': '24px',
          'sizeSectionTitle': '18px',
          'sizeSectionSubtitle': '12px',
          'weightNormal': '400',
          'weightMedium': '500',
          'weightSemibold': '600',
          'weightBold': '700',
          'lineHeightBase': '1.5',
          'lineHeightDense': '1.35'},
 'color': {'pageBackground': '#edf3f8',
           'cardBackground': '#ffffff',
           'headerBackground': '#f6f9fc',
           'headerBackgroundStrong': '#eef4f9',
           'tableStripeBackground': '#f8fbfd',
           'tableHeaderBackground': '#f3f7fb',
           'textPrimary': '#223548',
           'textHeading': '#0f2d45',
           'textMuted': '#5f7387',
           'textSubtle': '#6f8293',
           'textInverse': '#ffffff',
           'borderDefault': '#cdd9e5',
           'borderSoft': '#d9e4ee',
           'borderRow': '#e6edf3',
           'brandPrimary': '#005496',
           'brandAccent': '#5f7fa6',
           'trendUp': '#0b7a43',
           'trendDown': '#c04b39',
           'trendNeutral': '#6c7f91',
           'statusSuccess': '#0b7a43',
           'statusSuccessBackground': '#def4e7',
           'statusWarning': '#b7791f',
           'statusWarningBackground': '#f9eed7',
           'statusDanger': '#c04b39',
           'statusDangerBackground': '#fae2df',
           'statusNeutral': '#6c7f91',
           'statusNeutralBackground': '#eef3f7',
           'surface': {'page': '#edf3f8',
                       'canvas': '#f6f9fc',
                       'card': '#ffffff',
                       'cardMuted': '#f7fafd',
                       'header': '#f6f9fc',
                       'headerStrong': '#eef4f9',
                       'tableStripe': '#f8fbfd',
                       'tableHeader': '#f3f7fb',
                       'brandSoft': '#e4eff8',
                       'brandTint': '#f2f7fb',
                       'chartShell': '#fbfdff'},
           'text': {'primary': '#223548',
                    'heading': '#0f2d45',
                    'muted': '#5f7387',
                    'subtle': '#6f8293',
                    'inverse': '#ffffff',
                    'brand': '#005496'},
           'border': {'default': '#cdd9e5',
                      'soft': '#d9e4ee',
                      'row': '#e6edf3',
                      'strong': '#b8cada',
                      'brand': '#8bb0cb'},
           'brand': {'primary': '#005496',
                     'primaryStrong': '#003b6a',
                     'primarySoft': '#e4eff8',
                     'accent': '#5f7fa6',
                     'accentSoft': '#edf3f8'},
           'trend': {'up': '#0b7a43', 'down': '#c04b39', 'neutral': '#6c7f91'},
           'status': {'success': {'text': '#0b7a43', 'background': '#def4e7'},
                      'warning': {'text': '#b7791f', 'background': '#f9eed7'},
                      'danger': {'text': '#c04b39', 'background': '#fae2df'},
                      'neutral': {'text': '#6c7f91', 'background': '#eef3f7'}},
           'chart': {'palette': ['#005496',
                                 '#5f7fa6',
                                 '#5b9bd5',
                                 '#6f9a6d',
                                 '#d09a45',
                                 '#c65a4b',
                                 '#5ca7a4',
                                 '#7a6da8'],
                     'background': 'rgba(255,255,255,0)',
                     'title': '#0f2d45',
                     'subtitle': '#5f7387',
                     'legendText': '#556b7d',
                     'axisLine': '#b9c8d6',
                     'axisLabel': '#5f7387',
                     'splitLine': '#dfe7ef',
                     'toolboxBorder': '#7f97ab',
                     'series': {'current': '#005496',
                                'previous': '#5f7fa6',
                                'currentTint': 'rgba(0, 84, 150, 0.12)',
                                'previousTint': 'rgba(95, 127, 166, 0.08)'}},
           'area': {'total': {'barColor': '#005496', 'barTint': 'rgba(0, 84, 150, 0.12)'},
                    'diode': {'barColor': '#005496',
                              'barTint': 'rgba(0, 84, 150, 0.14)',
                              'headerBg': '#edf5fb',
                              'softBg': '#f8fbfe',
                              'strongBg': '#d7e7f4'},
                    'ico': {'barColor': '#6f9a6d',
                            'barTint': 'rgba(111, 154, 109, 0.16)',
                            'headerBg': '#f1f7f0',
                            'softBg': '#fbfdfb',
                            'strongBg': '#e2eedf'},
                    'sakari': {'barColor': '#d09a45',
                               'barTint': 'rgba(208, 154, 69, 0.16)',
                               'headerBg': '#fcf6ec',
                               'softBg': '#fffdf9',
                               'strongBg': '#f5e6cd'}}},
 'layout': {'pageMaxWidth': '1480px',
            'pagePadding': '0',
            'cardPadding': '16px',
            'cardGap': '16px',
            'sectionMarginTop': '24px',
            'tableCellPadding': '8px 10px',
            'tableCellPaddingDense': '4px 6px',
            'chartHeightDefault': '320px',
            'chartHeightCompact': '260px'},
 'radius': {'medium': '8px', 'large': '10px', 'pill': '999px'},
 'shadow': {'soft': '0 10px 24px rgba(15, 23, 42, 0.05)', 'card': '0 4px 12px rgba(15, 23, 42, 0.04)'},
 'spacing': {'xs': '4px', 'sm': '8px', 'md': '12px', 'lg': '16px', 'xl': '24px'},
 'components': {'page': {'background': '#edf3f8', 'textColor': '#223548'},
                'card': {'background': '#ffffff',
                         'borderColor': '#cdd9e5',
                         'borderRadius': '10px',
                         'padding': '16px',
                         'shadow': '0 6px 18px rgba(15, 46, 69, 0.05)'},
                'statusBadge': {'success': {'textColor': '#0b7a43',
                                            'background': '#def4e7',
                                            'borderColor': '#9fd6b0'},
                                'warning': {'textColor': '#b7791f',
                                            'background': '#f9eed7',
                                            'borderColor': '#e6c98f'},
                                'danger': {'textColor': '#c04b39',
                                           'background': '#fae2df',
                                           'borderColor': '#e6b1aa'},
                                'neutral': {'textColor': '#6c7f91',
                                            'background': '#eef3f7',
                                            'borderColor': '#cdd9e5'},
                                'info': {'textColor': '#005496',
                                         'background': '#e8f1f8',
                                         'borderColor': '#bfd4e5'}},
                'badge': {'textColor': '#5f7387',
                          'background': '#e7eef5',
                          'borderColor': '#cfdce8',
                          'fontSize': '10px',
                          'fontWeight': '800'},
                'trend': {'up': {'color': '#0b7a43'},
                          'down': {'color': '#c04b39'},
                          'neutral': {'color': '#6c7f91'}},
                'coverageNotice': {'background': '#f7fafc', 'borderColor': '#d9e4ee', 'textColor': '#6f8293'},
                'chartCard': {'background': '#fbfdff',
                              'borderColor': '#d9e4ee',
                              'borderRadius': '10px',
                              'padding': '16px',
                              'height': '320px',
                              'titleColor': '#0f2d45',
                              'subtitleColor': '#5f7387'},
                'chartNote': {'fontSize': '12px', 'fontWeight': '500', 'textColor': '#64748b'},
                'chartLegend': {'fontSize': '11px',
                                'fontWeight': '700',
                                'textColor': '#64748b',
                                'itemGap': '8px'},
                'chartMeta': {'valueColor': '#0f2d45',
                              'textColor': '#223548',
                              'subtleColor': '#6f8293',
                              'labelFontSize': '11px',
                              'smallFontSize': '9px'},
                'chartLayout': {'gridGap': '12px', 'subtitleMarginBottom': '10px', 'noteMarginTop': '10px'},
                'report': {'container': {'maxWidth': '1480px'},
                           'titleHeader': {'title': {'fontSize': '24px',
                                                     'fontWeight': '700',
                                                     'color': '#111827',
                                                     'letterSpacing': '0'},
                                           'subtitle': {'fontSize': '12px',
                                                        'fontWeight': '500',
                                                        'color': '#64748b'},
                                           'metadata': {'fontSize': '11px',
                                                        'fontWeight': '500',
                                                        'color': '#6b7280'},
                                           'banner': {'background': {'width': '110%',
                                                                     'height': '125%',
                                                                     'objectFit': 'cover',
                                                                     'objectPosition': 'center center'},
                                                      'overlay': {'minHeight': '132px',
                                                                  'gridTemplateColumns': '250px minmax(0, '
                                                                                         '1fr)',
                                                                  'padding': '0 300px 0 0'},
                                                      'logoSlot': {'alignItems': 'center',
                                                                   'justifyContent': 'flex-start',
                                                                   'paddingLeft': '34px'},
                                                      'logoCrop': {'width': '220px', 'height': '36px'},
                                                      'pdf': {'overlay': {'minHeight': '122px',
                                                                          'gridTemplateColumns': '250px '
                                                                                                 'minmax(0, '
                                                                                                 '1fr)',
                                                                          'padding': '0 182px 0 0'},
                                                              'logoSlot': {'paddingLeft': '22px'},
                                                              'logoCrop': {'width': '160px',
                                                                           'height': '24px'}}},
                                           'shell': {'background': '#ffffff',
                                                     'borderColor': '#cfe0ec',
                                                     'shadow': '0 12px 28px rgba(0, 84, 150, 0.12)',
                                                     'overlayGradient': 'linear-gradient(90deg, '
                                                                        'rgba(255,255,255,0.04) 0%, '
                                                                        'rgba(255,255,255,0.02) 36%, '
                                                                        'rgba(0,43,77,0.16) 100%)',
                                                     'dividerColor': 'rgba(0, 84, 150, 0.16)',
                                                     'dateChipBackground': 'rgba(255, 255, 255, 0.96)',
                                                     'dateChipBorderColor': '#cfe0ec',
                                                     'dateChipTextColor': '#0f2d45',
                                                     'dateChipMutedColor': '#5f7387',
                                                     'dateChipIconColor': '#005496',
                                                     'dateChipShadow': 'inset 0 0 0 1px rgba(0, 84, 150, '
                                                                       '0.08)'}},
                           'footer': {'textColor': '#6b7280', 'borderColor': '#d1d5db'},
                           'section': {'electric': {'card': {'total': {'layout': {'minHeight': '150px',
                                                                                  'padding': '11px 14px 10px',
                                                                                  'titleRowGap': '9px',
                                                                                  'primaryValueFontSize': '20px',
                                                                                  'footerGap': '6px',
                                                                                  'footerMarginTop': '8px'},
                                                                       'compare': {'blockMarginTop': '2px',
                                                                                   'padding': '7px 8px',
                                                                                   'itemMinHeight': '30px',
                                                                                   'labelFontSize': '10px',
                                                                                   'labelFontWeight': '800',
                                                                                   'labelColor': '#64748b',
                                                                                   'labelLetterSpacing': '0.05em',
                                                                                   'valueFontSize': '15px'},
                                                                       'pdf': {'height': '130px',
                                                                               'minHeight': '130px',
                                                                               'padding': '8px 9px',
                                                                               'borderRadius': '10px',
                                                                               'topGap': '6px',
                                                                               'topMarginBottom': '6px',
                                                                               'leadGap': '3px',
                                                                               'titleRowGap': '6px',
                                                                               'iconSize': '28px',
                                                                               'iconGlyphSize': '15px',
                                                                               'titleFontSize': '8px',
                                                                               'primaryGap': '4px',
                                                                               'primaryValueFontSize': '13px',
                                                                               'supportingFontSize': '7px',
                                                                               'metaMarginTop': '6px',
                                                                               'metaMarginBottom': '4px',
                                                                               'metaGap': '6px',
                                                                               'meterValueFontSize': '8.5px',
                                                                               'comparePadding': '5px 6px',
                                                                               'compareItemPadding': '2px '
                                                                                                     '5px',
                                                                               'compareLabelFontSize': '6.2px',
                                                                               'compareValueFontSize': '10px',
                                                                               'footerGap': '10px',
                                                                               'footerMarginTop': '4px',
                                                                               'footerRowGap': '2px',
                                                                               'footerPaddingTop': '2px',
                                                                               'deltaGap': '5px',
                                                                               'footerValueFontSize': '8.5px',
                                                                               'metaRowGap': '6px',
                                                                               'metaValueGap': '4px',
                                                                               'trendRowGap': '3px',
                                                                               'trendNoteFontSize': '6.4px'}},
                                                             'diode': {'layout': {'minHeight': '150px',
                                                                                  'padding': '11px 14px 10px',
                                                                                  'titleRowGap': '9px',
                                                                                  'primaryValueFontSize': '20px',
                                                                                  'footerGap': '6px',
                                                                                  'footerMarginTop': '8px'},
                                                                       'compare': {'blockMarginTop': '2px',
                                                                                   'padding': '7px 8px',
                                                                                   'itemMinHeight': '30px',
                                                                                   'labelFontSize': '10px',
                                                                                   'labelFontWeight': '800',
                                                                                   'labelColor': '#64748b',
                                                                                   'labelLetterSpacing': '0.05em',
                                                                                   'valueFontSize': '15px'},
                                                                       'pdf': {'height': '130px',
                                                                               'minHeight': '130px',
                                                                               'padding': '8px 9px',
                                                                               'borderRadius': '10px',
                                                                               'topGap': '6px',
                                                                               'topMarginBottom': '6px',
                                                                               'leadGap': '3px',
                                                                               'titleRowGap': '6px',
                                                                               'iconSize': '28px',
                                                                               'iconGlyphSize': '15px',
                                                                               'titleFontSize': '8px',
                                                                               'primaryGap': '4px',
                                                                               'primaryValueFontSize': '13px',
                                                                               'supportingFontSize': '7px',
                                                                               'metaMarginTop': '6px',
                                                                               'metaMarginBottom': '4px',
                                                                               'metaGap': '6px',
                                                                               'meterValueFontSize': '8.5px',
                                                                               'comparePadding': '5px 6px',
                                                                               'compareItemPadding': '2px '
                                                                                                     '5px',
                                                                               'compareLabelFontSize': '6.2px',
                                                                               'compareValueFontSize': '10px',
                                                                               'footerGap': '10px',
                                                                               'footerMarginTop': '4px',
                                                                               'footerRowGap': '2px',
                                                                               'footerPaddingTop': '2px',
                                                                               'deltaGap': '5px',
                                                                               'footerValueFontSize': '8.5px',
                                                                               'metaRowGap': '6px',
                                                                               'metaValueGap': '4px',
                                                                               'trendRowGap': '3px',
                                                                               'trendNoteFontSize': '6.4px'}},
                                                             'ico': {'layout': {'minHeight': '150px',
                                                                                'padding': '11px 14px 10px',
                                                                                'titleRowGap': '9px',
                                                                                'primaryValueFontSize': '20px',
                                                                                'footerGap': '6px',
                                                                                'footerMarginTop': '8px'},
                                                                     'compare': {'blockMarginTop': '2px',
                                                                                 'padding': '7px 8px',
                                                                                 'itemMinHeight': '30px',
                                                                                 'labelFontSize': '10px',
                                                                                 'labelFontWeight': '800',
                                                                                 'labelColor': '#64748b',
                                                                                 'labelLetterSpacing': '0.05em',
                                                                                 'valueFontSize': '15px'},
                                                                     'pdf': {'height': '130px',
                                                                             'minHeight': '130px',
                                                                             'padding': '8px 9px',
                                                                             'borderRadius': '10px',
                                                                             'topGap': '6px',
                                                                             'topMarginBottom': '6px',
                                                                             'leadGap': '3px',
                                                                             'titleRowGap': '6px',
                                                                             'iconSize': '28px',
                                                                             'iconGlyphSize': '15px',
                                                                             'titleFontSize': '8px',
                                                                             'primaryGap': '4px',
                                                                             'primaryValueFontSize': '13px',
                                                                             'supportingFontSize': '7px',
                                                                             'metaMarginTop': '6px',
                                                                             'metaMarginBottom': '4px',
                                                                             'metaGap': '6px',
                                                                             'meterValueFontSize': '8.5px',
                                                                             'comparePadding': '5px 6px',
                                                                             'compareItemPadding': '2px 5px',
                                                                             'compareLabelFontSize': '6.2px',
                                                                             'compareValueFontSize': '10px',
                                                                             'footerGap': '10px',
                                                                             'footerMarginTop': '4px',
                                                                             'footerRowGap': '2px',
                                                                             'footerPaddingTop': '2px',
                                                                             'deltaGap': '5px',
                                                                             'footerValueFontSize': '8.5px',
                                                                             'metaRowGap': '6px',
                                                                             'metaValueGap': '4px',
                                                                             'trendRowGap': '3px',
                                                                             'trendNoteFontSize': '6.4px'}},
                                                             'sakari': {'layout': {'minHeight': '150px',
                                                                                   'padding': '11px 14px '
                                                                                              '10px',
                                                                                   'titleRowGap': '9px',
                                                                                   'primaryValueFontSize': '20px',
                                                                                   'footerGap': '6px',
                                                                                   'footerMarginTop': '8px'},
                                                                        'compare': {'blockMarginTop': '2px',
                                                                                    'padding': '7px 8px',
                                                                                    'itemMinHeight': '30px',
                                                                                    'labelFontSize': '10px',
                                                                                    'labelFontWeight': '800',
                                                                                    'labelColor': '#64748b',
                                                                                    'labelLetterSpacing': '0.05em',
                                                                                    'valueFontSize': '15px'},
                                                                        'pdf': {'height': '130px',
                                                                                'minHeight': '130px',
                                                                                'padding': '8px 9px',
                                                                                'borderRadius': '10px',
                                                                                'topGap': '6px',
                                                                                'topMarginBottom': '6px',
                                                                                'leadGap': '3px',
                                                                                'titleRowGap': '6px',
                                                                                'iconSize': '28px',
                                                                                'iconGlyphSize': '15px',
                                                                                'titleFontSize': '8px',
                                                                                'primaryGap': '4px',
                                                                                'primaryValueFontSize': '13px',
                                                                                'supportingFontSize': '7px',
                                                                                'metaMarginTop': '6px',
                                                                                'metaMarginBottom': '4px',
                                                                                'metaGap': '6px',
                                                                                'meterValueFontSize': '8.5px',
                                                                                'comparePadding': '5px 6px',
                                                                                'compareItemPadding': '2px '
                                                                                                      '5px',
                                                                                'compareLabelFontSize': '6.2px',
                                                                                'compareValueFontSize': '10px',
                                                                                'footerGap': '10px',
                                                                                'footerMarginTop': '4px',
                                                                                'footerRowGap': '2px',
                                                                                'footerPaddingTop': '2px',
                                                                                'deltaGap': '5px',
                                                                                'footerValueFontSize': '8.5px',
                                                                                'metaRowGap': '6px',
                                                                                'metaValueGap': '4px',
                                                                                'trendRowGap': '3px',
                                                                                'trendNoteFontSize': '6.4px'}},
                                                             'theme': {'base': {'accent': '#005496',
                                                                                'borderColor': '#bfd4e5',
                                                                                'surface': 'linear-gradient(135deg, '
                                                                                           'rgba(0, 84, 150, '
                                                                                           '0.10) 0%, '
                                                                                           'rgba(248, 251, '
                                                                                           '254, 0.94) 55%, '
                                                                                           'rgba(255, 255, '
                                                                                           '255, 0.99) 100%)',
                                                                                'shadow': '0 12px 22px '
                                                                                          'rgba(0, 84, 150, '
                                                                                          '0.08)',
                                                                                'titleColor': '#003b6a',
                                                                                'copyColor': '#6f8293',
                                                                                'currentColor': '#005496',
                                                                                'previousColor': '#5f7fa6',
                                                                                'noteColor': '#6f8293',
                                                                                'iconBackground': 'linear-gradient(180deg, '
                                                                                                  '#0d67a8 '
                                                                                                  '0%, '
                                                                                                  '#005496 '
                                                                                                  '100%)',
                                                                                'iconColor': '#ffffff',
                                                                                'primaryColor': '#005496',
                                                                                'primaryUnitColor': '#0f2d45',
                                                                                'compareBackground': 'rgba(255, '
                                                                                                     '255, '
                                                                                                     '255, '
                                                                                                     '0.94)',
                                                                                'compareBorderColor': 'rgba(191, '
                                                                                                      '212, '
                                                                                                      '229, '
                                                                                                      '0.95)',
                                                                                'compareDividerColor': 'rgba(214, '
                                                                                                       '226, '
                                                                                                       '236, '
                                                                                                       '0.95)'},
                                                                       'total': {'accent': '#005496',
                                                                                 'borderColor': '#2e72a4',
                                                                                 'surface': 'linear-gradient(135deg, '
                                                                                            '#005496 0%, '
                                                                                            '#0a6aae 100%)',
                                                                                 'shadow': '0 16px 28px '
                                                                                           'rgba(0, 84, 150, '
                                                                                           '0.22)',
                                                                                 'titleColor': '#ffffff',
                                                                                 'copyColor': 'rgba(255, '
                                                                                              '255, 255, '
                                                                                              '0.84)',
                                                                                 'currentColor': '#ffffff',
                                                                                 'previousColor': '#dbeafe',
                                                                                 'noteColor': 'rgba(255, '
                                                                                              '255, 255, '
                                                                                              '0.88)',
                                                                                 'iconBackground': '#ffffff',
                                                                                 'iconColor': '#005496',
                                                                                 'primaryColor': '#ffffff',
                                                                                 'primaryUnitColor': 'rgba(255, '
                                                                                                     '255, '
                                                                                                     '255, '
                                                                                                     '0.94)',
                                                                                 'compareBackground': 'rgba(255, '
                                                                                                      '255, '
                                                                                                      '255, '
                                                                                                      '0.98)',
                                                                                 'compareBorderColor': 'rgba(213, '
                                                                                                       '228, '
                                                                                                       '242, '
                                                                                                       '0.96)',
                                                                                 'compareDividerColor': 'rgba(221, '
                                                                                                        '232, '
                                                                                                        '242, '
                                                                                                        '0.92)'},
                                                                       'diode': {'accent': '#005496',
                                                                                 'borderColor': '#c3d8e8',
                                                                                 'surface': 'linear-gradient(135deg, '
                                                                                            'rgba(0, 84, '
                                                                                            '150, 0.11) 0%, '
                                                                                            'rgba(247, 251, '
                                                                                            '255, 0.94) 56%, '
                                                                                            'rgba(255, 255, '
                                                                                            '255, 0.99) '
                                                                                            '100%)',
                                                                                 'shadow': '0 12px 22px '
                                                                                           'rgba(0, 84, 150, '
                                                                                           '0.08)',
                                                                                 'titleColor': '#003b6a',
                                                                                 'copyColor': '#6f8293',
                                                                                 'currentColor': '#005496',
                                                                                 'previousColor': '#5f7fa6',
                                                                                 'noteColor': '#6f8293',
                                                                                 'iconBackground': 'linear-gradient(180deg, '
                                                                                                   '#0d67a8 '
                                                                                                   '0%, '
                                                                                                   '#005496 '
                                                                                                   '100%)',
                                                                                 'iconColor': '#ffffff',
                                                                                 'primaryColor': '#005496',
                                                                                 'primaryUnitColor': '#0f2d45',
                                                                                 'compareBackground': 'rgba(255, '
                                                                                                      '255, '
                                                                                                      '255, '
                                                                                                      '0.94)',
                                                                                 'compareBorderColor': 'rgba(191, '
                                                                                                       '212, '
                                                                                                       '229, '
                                                                                                       '0.95)',
                                                                                 'compareDividerColor': 'rgba(214, '
                                                                                                        '226, '
                                                                                                        '236, '
                                                                                                        '0.95)'},
                                                                       'ico': {'accent': '#6f9a6d',
                                                                               'borderColor': '#cadfc8',
                                                                               'surface': 'linear-gradient(135deg, '
                                                                                          'rgba(111, 154, '
                                                                                          '109, 0.12) 0%, '
                                                                                          'rgba(249, 252, '
                                                                                          '249, 0.94) 56%, '
                                                                                          'rgba(255, 255, '
                                                                                          '255, 0.99) 100%)',
                                                                               'shadow': '0 12px 22px '
                                                                                         'rgba(0, 84, 150, '
                                                                                         '0.08)',
                                                                               'titleColor': '#4f7750',
                                                                               'copyColor': '#6f8293',
                                                                               'currentColor': '#005496',
                                                                               'previousColor': '#5f7fa6',
                                                                               'noteColor': '#6f8293',
                                                                               'iconBackground': 'linear-gradient(180deg, '
                                                                                                 '#82a97f '
                                                                                                 '0%, '
                                                                                                 '#6f9a6d '
                                                                                                 '100%)',
                                                                               'iconColor': '#ffffff',
                                                                               'primaryColor': '#005496',
                                                                               'primaryUnitColor': '#0f2d45',
                                                                               'compareBackground': 'rgba(255, '
                                                                                                    '255, '
                                                                                                    '255, '
                                                                                                    '0.94)',
                                                                               'compareBorderColor': 'rgba(191, '
                                                                                                     '212, '
                                                                                                     '229, '
                                                                                                     '0.95)',
                                                                               'compareDividerColor': 'rgba(214, '
                                                                                                      '226, '
                                                                                                      '236, '
                                                                                                      '0.95)'},
                                                                       'sakari': {'accent': '#d09a45',
                                                                                  'borderColor': '#e4d3b3',
                                                                                  'surface': 'linear-gradient(135deg, '
                                                                                             'rgba(208, 154, '
                                                                                             '69, 0.13) 0%, '
                                                                                             'rgba(254, 251, '
                                                                                             '246, 0.95) '
                                                                                             '56%, rgba(255, '
                                                                                             '255, 255, '
                                                                                             '0.99) 100%)',
                                                                                  'shadow': '0 12px 22px '
                                                                                            'rgba(0, 84, '
                                                                                            '150, 0.08)',
                                                                                  'titleColor': '#9c6a22',
                                                                                  'copyColor': '#6f8293',
                                                                                  'currentColor': '#005496',
                                                                                  'previousColor': '#5f7fa6',
                                                                                  'noteColor': '#6f8293',
                                                                                  'iconBackground': 'linear-gradient(180deg, '
                                                                                                    '#d7a857 '
                                                                                                    '0%, '
                                                                                                    '#d09a45 '
                                                                                                    '100%)',
                                                                                  'iconColor': '#ffffff',
                                                                                  'primaryColor': '#005496',
                                                                                  'primaryUnitColor': '#0f2d45',
                                                                                  'compareBackground': 'rgba(255, '
                                                                                                       '255, '
                                                                                                       '255, '
                                                                                                       '0.94)',
                                                                                  'compareBorderColor': 'rgba(191, '
                                                                                                        '212, '
                                                                                                        '229, '
                                                                                                        '0.95)',
                                                                                  'compareDividerColor': 'rgba(214, '
                                                                                                         '226, '
                                                                                                         '236, '
                                                                                                         '0.95)'}}},
                                                    'chart': {'dailyTrend': {'legend': {'bottom': 'center'},
                                                                             'grid': {'left': 20,
                                                                                      'right': 12,
                                                                                      'top': 20,
                                                                                      'bottom': 15,
                                                                                      'containLabel': True},
                                                                             'height': {'view': {'default': '340px',
                                                                                                 'periodic': '356px',
                                                                                                 'weekly': '392px',
                                                                                                 'monthly': '130px'},
                                                                                        'pdf': {'default': '216px',
                                                                                                'periodic': '224px',
                                                                                                'weekly': '244px',
                                                                                                'monthly': '130px'}}},
                                                              'areaComparison': {'legend': {'bottom': 'center'},
                                                                                 'grid': {'left': 25,
                                                                                          'right': 12,
                                                                                          'top': 20,
                                                                                          'bottom': 15,
                                                                                          'containLabel': True},
                                                                                 'height': {'view': {'default': '340px',
                                                                                                     'periodic': '356px',
                                                                                                     'weekly': '392px',
                                                                                                     'monthly': '130px'},
                                                                                            'pdf': {'default': '240px',
                                                                                                    'periodic': '240px',
                                                                                                    'weekly': '244px',
                                                                                                    'monthly': '130px'}}},
                                                              'areaShare': {'legend': {'bottom': 'center',
                                                                                       'orient': 'horizontal',
                                                                                       'left': 'center',
                                                                                       'top': '3%',
                                                                                       'itemWidth': 14,
                                                                                       'itemHeight': 14,
                                                                                       'icon': 'roundRect',
                                                                                       'itemGap': 12,
                                                                                       'textStyle': {'color': '#475569',
                                                                                                     'fontSize': 10,
                                                                                                     'fontWeight': 500}},
                                                                            'pie': {'radius': ['39%', '60%'],
                                                                                    'center': ['50%', '50%'],
                                                                                    'sliceBorderRadius': 6},
                                                                            'centerGraphic': {'left': '43%',
                                                                                              'top': '45%',
                                                                                              'valueFontSize': 12,
                                                                                              'titleFontSize': 8,
                                                                                              'unitFontSize': 7,
                                                                                              'titleY': 15,
                                                                                              'unitY': 24},
                                                                            'height': {'view': {'default': '340px'},
                                                                                       'pdf': {'default': '240px'}}},
                                                              'heatmap': {'height': {'view': {'default': '228px',
                                                                                              'weekly': '252px',
                                                                                              'monthly': '130px'},
                                                                                     'pdf': {'default': '156px',
                                                                                             'weekly': '184px',
                                                                                             'monthly': '130px'}},
                                                                          'grid': {'default': {'left': 58,
                                                                                               'right': 18,
                                                                                               'top': 10,
                                                                                               'bottom': 30,
                                                                                               'containLabel': False},
                                                                                   'dense': {'left': 58,
                                                                                             'right': 18,
                                                                                             'top': 10,
                                                                                             'bottom': 62,
                                                                                             'containLabel': False},
                                                                                   'monthly': {'left': 18,
                                                                                               'right': 18,
                                                                                               'top': 10,
                                                                                               'bottom': 62,
                                                                                               'containLabel': False}}},
                                                              'delta': {'grid': {'left': 52,
                                                                                 'right': 32,
                                                                                 'top': 8,
                                                                                 'bottom': 15,
                                                                                 'containLabel': False},
                                                                        'height': {'view': {'periodic': '252px',
                                                                                            'monthly': '130px',
                                                                                            'default': '228px',
                                                                                            'weekly': '252px'},
                                                                                   'pdf': {'periodic': '178px',
                                                                                           'monthly': '130px',
                                                                                           'default': '156px',
                                                                                           'weekly': '184px'}}},
                                                              'theme': {'series': {'current': '#005496',
                                                                                   'previous': '#5f7fa6',
                                                                                   'currentTint': 'rgba(0, '
                                                                                                  '84, 150, '
                                                                                                  '0.12)',
                                                                                   'previousTint': 'rgba(95, '
                                                                                                   '127, '
                                                                                                   '166, '
                                                                                                   '0.08)'},
                                                                        'delta': {'total': '#005496'}}},
                                                    'table': {'common': {'headerBackground': '#f8fafc',
                                                                         'stripeBackground': '#fafafa',
                                                                         'borderColor': '#e5e7eb',
                                                                         'textColor': '#1f2937',
                                                                         'headerTextColor': '#111827',
                                                                         'cellPadding': '8px 10px',
                                                                         'denseCellPadding': '4px 6px'}},
                                                    'header': {'padding': '7px 11px 6px',
                                                               'shellGap': '12px',
                                                               'mainGap': '10px',
                                                               'iconSize': '45px',
                                                               'iconGlyphSize': '25px',
                                                               'titleLetterSpacing': '0.01em',
                                                               'subtitleMarginTop': '1px',
                                                               'dateChipMinWidth': '228px'}},
                                       'utility': {'card': {'totalUtility': {'layout': {'minHeight': '154px',
                                                                                        'padding': '12px '
                                                                                                   '13px',
                                                                                        'topGap': '10px',
                                                                                        'primaryValueFontSize': '20px',
                                                                                        'deltaPaddingTop': '8px'},
                                                                             'compare': {'blockMarginTop': '2px',
                                                                                         'padding': '7px 8px',
                                                                                         'itemMinHeight': '30px',
                                                                                         'labelFontSize': '10px',
                                                                                         'labelFontWeight': '800',
                                                                                         'labelColor': '#64748b',
                                                                                         'labelLetterSpacing': '0.05em',
                                                                                         'valueFontSize': '15px'}},
                                                            'airEnergy': {'layout': {'minHeight': '154px',
                                                                                     'padding': '12px 13px',
                                                                                     'topGap': '10px',
                                                                                     'primaryValueFontSize': '20px',
                                                                                     'deltaPaddingTop': '8px'},
                                                                          'compare': {'blockMarginTop': '2px',
                                                                                      'padding': '7px 8px',
                                                                                      'itemMinHeight': '30px',
                                                                                      'labelFontSize': '10px',
                                                                                      'labelFontWeight': '800',
                                                                                      'labelColor': '#64748b',
                                                                                      'labelLetterSpacing': '0.05em',
                                                                                      'valueFontSize': '15px'}},
                                                            'chilledWaterEnergy': {'layout': {'minHeight': '154px',
                                                                                              'padding': '12px '
                                                                                                         '13px',
                                                                                              'topGap': '10px',
                                                                                              'primaryValueFontSize': '20px',
                                                                                              'deltaPaddingTop': '8px'},
                                                                                   'compare': {'blockMarginTop': '2px',
                                                                                               'padding': '7px '
                                                                                                          '8px',
                                                                                               'itemMinHeight': '30px',
                                                                                               'labelFontSize': '10px',
                                                                                               'labelFontWeight': '800',
                                                                                               'labelColor': '#64748b',
                                                                                               'labelLetterSpacing': '0.05em',
                                                                                               'valueFontSize': '15px'}},
                                                            'boilerEnergy': {'layout': {'minHeight': '154px',
                                                                                        'padding': '12px '
                                                                                                   '13px',
                                                                                        'topGap': '10px',
                                                                                        'primaryValueFontSize': '20px',
                                                                                        'deltaPaddingTop': '8px'},
                                                                             'compare': {'blockMarginTop': '2px',
                                                                                         'padding': '7px 8px',
                                                                                         'itemMinHeight': '30px',
                                                                                         'labelFontSize': '10px',
                                                                                         'labelFontWeight': '800',
                                                                                         'labelColor': '#64748b',
                                                                                         'labelLetterSpacing': '0.05em',
                                                                                         'valueFontSize': '15px'}}},
                                                   'chart': {'comparison': {'legend': {'bottom': 'center'},
                                                                            'grid': {'left': 28,
                                                                                     'right': 10,
                                                                                     'top': 10,
                                                                                     'bottom': 20,
                                                                                     'containLabel': True},
                                                                            'height': {'view': '272px',
                                                                                       'pdf': '140px'}},
                                                             'periodTrend': {'height': {'view': '326px',
                                                                                        'pdf': '228px'}},
                                                             'typeTrend': {'legend': {'top': 'left'},
                                                                           'grid': {'left': 32,
                                                                                    'right': 10,
                                                                                    'top': 36,
                                                                                    'bottom': 46,
                                                                                    'containLabel': True},
                                                                           'height': {'view': '292px',
                                                                                      'pdf': '186px'}},
                                                             'mix': {'legend': {'bottom': 'center'}},
                                                             'energyTrend': {'legend': {'top': 'left'},
                                                                             'grid': {'left': 18,
                                                                                      'right': 12,
                                                                                      'top': 44,
                                                                                      'bottom': 52,
                                                                                      'containLabel': True},
                                                                             'height': {'view': '308px',
                                                                                        'pdf': '220px'}},
                                                             'periodSensorTrend': {'legend': {'top': 'left'},
                                                                                   'grid': {'left': 20,
                                                                                            'right': 16,
                                                                                            'top': 54,
                                                                                            'bottom': 30,
                                                                                            'containLabel': True},
                                                                                   'height': {'view': '220px',
                                                                                              'pdf': {'default': '156px',
                                                                                                      'single': '142px'}}},
                                                             'sensorCluster': {'legend': {'bottom': 'center'},
                                                                               'grid': {'left': 20,
                                                                                        'right': 8,
                                                                                        'top': 25,
                                                                                        'bottom': 20,
                                                                                        'containLabel': True},
                                                                               'height': {'view': '280px',
                                                                                          'pdf': '140px'}},
                                                             'deviation': {'grid': {'left': 92,
                                                                                    'right': 24,
                                                                                    'top': 10,
                                                                                    'bottom': 28},
                                                                           'height': {'view': '326px',
                                                                                      'pdf': '150px'},
                                                                           'valueLabel': {'positivePosition': 'right',
                                                                                          'negativePosition': 'left',
                                                                                          'distance': 4,
                                                                                          'fontSize': 10,
                                                                                          'fontWeight': 700,
                                                                                          'color': '#334155',
                                                                                          'axisPaddingLeft': 30,
                                                                                          'axisPaddingRight': 30}}},
                                                   'table': {'common': {'headerBackground': '#f8fafc',
                                                                        'stripeBackground': '#fafafa',
                                                                        'borderColor': '#e5e7eb',
                                                                        'textColor': '#1f2937',
                                                                        'headerTextColor': '#111827',
                                                                        'cellPadding': '8px 10px',
                                                                        'denseCellPadding': '4px 6px'}}},
                                       'kpi': {'card': {'total': {'layout': {'minHeight': '172px',
                                                                             'padding': '12px 14px 12px',
                                                                             'topGap': '10px',
                                                                             'footerMarginTop': '12px'},
                                                                  'compare': {'blockMarginTop': '2px',
                                                                              'padding': '7px 8px',
                                                                              'itemMinHeight': '30px',
                                                                              'labelFontSize': '10px',
                                                                              'labelFontWeight': '800',
                                                                              'labelColor': '#64748b',
                                                                              'labelLetterSpacing': '0.05em',
                                                                              'valueFontSize': '15px'}},
                                                        'plant': {'layout': {'minHeight': '172px',
                                                                             'padding': '12px 14px 12px',
                                                                             'topGap': '10px',
                                                                             'footerMarginTop': '12px'},
                                                                  'compare': {'blockMarginTop': '2px',
                                                                              'padding': '7px 8px',
                                                                              'itemMinHeight': '30px',
                                                                              'labelFontSize': '10px',
                                                                              'labelFontWeight': '800',
                                                                              'labelColor': '#64748b',
                                                                              'labelLetterSpacing': '0.05em',
                                                                              'valueFontSize': '15px'}},
                                                        'diode': {'layout': {'minHeight': '172px',
                                                                             'padding': '12px 14px 12px',
                                                                             'topGap': '10px',
                                                                             'footerMarginTop': '12px'},
                                                                  'compare': {'blockMarginTop': '2px',
                                                                              'padding': '7px 8px',
                                                                              'itemMinHeight': '30px',
                                                                              'labelFontSize': '10px',
                                                                              'labelFontWeight': '800',
                                                                              'labelColor': '#64748b',
                                                                              'labelLetterSpacing': '0.05em',
                                                                              'valueFontSize': '15px'}},
                                                        'ico': {'layout': {'minHeight': '172px',
                                                                           'padding': '12px 14px 12px',
                                                                           'topGap': '10px',
                                                                           'footerMarginTop': '12px'},
                                                                'compare': {'blockMarginTop': '2px',
                                                                            'padding': '7px 8px',
                                                                            'itemMinHeight': '30px',
                                                                            'labelFontSize': '10px',
                                                                            'labelFontWeight': '800',
                                                                            'labelColor': '#64748b',
                                                                            'labelLetterSpacing': '0.05em',
                                                                            'valueFontSize': '15px'}},
                                                        'sakari': {'layout': {'minHeight': '172px',
                                                                              'padding': '12px 14px 12px',
                                                                              'topGap': '10px',
                                                                              'footerMarginTop': '12px'},
                                                                   'compare': {'blockMarginTop': '2px',
                                                                               'padding': '7px 8px',
                                                                               'itemMinHeight': '30px',
                                                                               'labelFontSize': '10px',
                                                                               'labelFontWeight': '800',
                                                                               'labelColor': '#64748b',
                                                                               'labelLetterSpacing': '0.05em',
                                                                               'valueFontSize': '15px'}}},
                                               'chart': {'dashboard': {'height': {'view': '288px',
                                                                                  'pdf': '196px'}},
                                                         'compareBar': {'legend': {'top': 'left'},
                                                                        'grid': {'left': 32,
                                                                                 'right': 12,
                                                                                 'top': 20,
                                                                                 'bottom': 25,
                                                                                 'containLabel': True}},
                                                         'waterfall': {'grid': {'left': 32,
                                                                                'right': 12,
                                                                                'top': 20,
                                                                                'bottom': 25,
                                                                                'containLabel': True}},
                                                         'variance': {'grid': {'left': 70,
                                                                               'right': 16,
                                                                               'top': 12,
                                                                               'bottom': 18,
                                                                               'containLabel': False}}},
                                               'table': {'common': {'headerBackground': '#f8fafc',
                                                                    'stripeBackground': '#fafafa',
                                                                    'borderColor': '#e5e7eb',
                                                                    'textColor': '#1f2937',
                                                                    'headerTextColor': '#111827',
                                                                    'cellPadding': '8px 10px',
                                                                    'denseCellPadding': '4px 6px'},
                                                         'summaryMatrix': {'width': {'view': '1440px',
                                                                                     'pdf': '100%'},
                                                                           'metricColumnWidth': {'view': '160px',
                                                                                                 'pdf': '110px'},
                                                                           'groupHeaderPaddingY': {'view': '12px',
                                                                                                   'pdf': '12px'},
                                                                           'groupSubheaderPaddingY': {'view': '10px',
                                                                                                      'pdf': '10px'},
                                                                           'groupDividerWidth': {'view': '3px',
                                                                                                 'pdf': '3px'}},
                                                         'dailyDetail': {'cellPadding': {'view': '7px 8px',
                                                                                         'pdf': '4px 4px'},
                                                                         'cellFontSize': {'view': '11px',
                                                                                          'pdf': '7.5px'},
                                                                         'dateColumnWidth': {'view': '108px',
                                                                                             'pdf': '78px'},
                                                                         'sourceColumnWidth': {'view': '56px',
                                                                                               'pdf': '42px'},
                                                                         'areaColumnWidth': {'view': '74px',
                                                                                             'pdf': '52px'},
                                                                         'metricFontSize': {'view': '10.75px',
                                                                                            'pdf': '7.25px'},
                                                                         'areaBackground': '#f8fbff',
                                                                         'submetricBorderColor': '#eef4fa',
                                                                         'groupEndBorderColor': '#dbeafe',
                                                                         'groupEndBorderWidth': {'view': '2px',
                                                                                                 'pdf': '1.5px'}}},
                                               'header': {'padding': '8px 12px 7px',
                                                          'shellGap': '14px',
                                                          'mainGap': '12px',
                                                          'iconSize': '50px',
                                                          'iconGlyphSize': '28px',
                                                          'titleLetterSpacing': '0.01em',
                                                          'subtitleMarginTop': '2px',
                                                          'dateChipMinWidth': '228px'}},
                                       'common': {'table': {'base': {'headerBackground': '#f8fafc',
                                                                     'stripeBackground': '#fafafa',
                                                                     'borderColor': '#e5e7eb',
                                                                     'textColor': '#1f2937',
                                                                     'headerTextColor': '#111827',
                                                                     'cellPadding': '8px 10px',
                                                                     'denseCellPadding': '4px 6px'}},
                                                  'card': {'gridGap': '16px',
                                                           'borderRadius': '16px',
                                                           'compare': {'blockMarginTop': '2px',
                                                                       'padding': '7px 8px',
                                                                       'itemMinHeight': '30px',
                                                                       'labelFontSize': '10px',
                                                                       'labelFontWeight': '800',
                                                                       'labelColor': '#64748b',
                                                                       'labelLetterSpacing': '0.05em',
                                                                       'valueFontSize': '15px'}},
                                                  'header': {'padding': '7px 11px 6px',
                                                             'shellGap': '12px',
                                                             'mainGap': '10px',
                                                             'iconSize': '45px',
                                                             'iconGlyphSize': '25px',
                                                             'titleLetterSpacing': '0.01em',
                                                             'subtitleMarginTop': '1px',
                                                             'dateChipMinWidth': '228px',
                                                             'background': '#f6f9fc',
                                                             'borderColor': '#cdd9e5',
                                                             'accentColor': '#005496',
                                                             'titleColor': '#0f2d45',
                                                             'subtitleColor': '#5f7387',
                                                             'dateChipBackground': 'rgba(255, 255, 255, '
                                                                                   '0.94)',
                                                             'dateChipBorderColor': '#cfe0ec',
                                                             'dateChipTextColor': '#0f2d45',
                                                             'dateChipMutedColor': '#5f7387',
                                                             'dateChipIconColor': '#005496',
                                                             'dateChipShadow': 'inset 0 0 0 1px rgba(0, 84, '
                                                                               '150, 0.08)'}}}},
                'sectionHeader': {'titleFontSize': '18px',
                                  'titleFontWeight': '700',
                                  'titleColor': '#0f2d45',
                                  'subtitleFontSize': '12px',
                                  'subtitleColor': '#5f7387',
                                  'background': '#f6f9fc',
                                  'borderColor': '#cdd9e5',
                                  'accentColor': '#005496'}},
 'echartsTheme': {'themeName': 'report_default',
                  'palette': ['#005496',
                              '#5f7fa6',
                              '#5b9bd5',
                              '#6f9a6d',
                              '#d09a45',
                              '#c65a4b',
                              '#5ca7a4',
                              '#7a6da8'],
                  'backgroundColor': 'rgba(255,255,255,0)',
                  'titleColor': '#0f2d45',
                  'subtitleColor': '#5f7387',
                  'legendTextColor': '#556b7d',
                  'axisLineColor': '#b9c8d6',
                  'axisLabelColor': '#5f7387',
                  'splitLineColor': '#dfe7ef',
                  'toolboxIconBorderColor': '#7f97ab',
                  'grid': {'left': '10%', 'right': '10%', 'top': 20, 'bottom': 15}}}

class ReportStyleService:
    """Load centralized style tokens and build inline render context."""

    def __init__(self, style_config_path: str | Path | None = None) -> None:
        self._style_config_path = Path(style_config_path or "config/report_style.json")
        self._warnings: list[str] = []

    def build_render_context(self) -> dict[str, Any]:
        """Build render-ready style context for Jinja templates."""
        style_config = self.load_style_config()
        theme = self.build_echarts_theme(style_config)

        return {
            "report_style": style_config,
            "report_style_css": self.build_inline_css(style_config),
            "chart_theme_name": theme["theme_name"],
            "chart_theme": theme["theme"],
            "chart_theme_json": json.dumps(theme["theme"], ensure_ascii=False),
            "report_style_config_path": str(self._style_config_path),
            "report_style_warnings": list(self._warnings),
        }

    def load_style_config(self) -> dict[str, Any]:
        """Load JSON style config and merge it over safe defaults."""
        defaults = deepcopy(DEFAULT_REPORT_STYLE)

        if not self._style_config_path.exists():
            self._warn(
                f"Style config not found at {self._style_config_path}. Falling back to defaults."
            )
            return defaults

        try:
            with self._style_config_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            self._warn(
                f"Invalid JSON in {self._style_config_path}: {exc}. Falling back to defaults."
            )
            return defaults
        except OSError as exc:
            self._warn(
                f"Failed to read {self._style_config_path}: {exc}. Falling back to defaults."
            )
            return defaults

        raw_style = payload.get("reportStyle")
        if not isinstance(raw_style, dict):
            self._warn(
                f"Top-level key 'reportStyle' is missing or invalid in {self._style_config_path}. Falling back to defaults."
            )
            return defaults

        merged = self._merge_defaults(defaults, raw_style)
        self._normalize_component_schema(merged)
        self._validate_minimum_shape(merged)
        return merged

    def build_inline_css(self, style_config: dict[str, Any]) -> str:
        """Convert the style config into inline CSS variables plus compatibility aliases."""
        sections_for_css = [
            "font",
            "color",
            "layout",
            "radius",
            "shadow",
            "spacing",
            "components",
        ]

        var_lines: list[str] = []
        for section_name in sections_for_css:
            section_value = style_config.get(section_name)
            if isinstance(section_value, dict):
                var_lines.extend(
                    self._flatten_css_variables(section_value, [self._to_kebab_case(section_name)])
                )

        alias_lines = self._build_compatibility_aliases(style_config)

        blocks = [":root {"]
        blocks.extend(f"    {line}" for line in var_lines)
        blocks.append("")
        blocks.extend(f"    {line}" for line in alias_lines)
        blocks.append("}")
        return "\n".join(blocks)

    def build_echarts_theme(self, style_config: dict[str, Any]) -> dict[str, Any]:
        """Build a Jinja-safe ECharts theme object from style tokens."""
        font_cfg = style_config.get("font", {})
        chart_cfg = style_config.get("echartsTheme", {})
        derived_theme = self._derive_echarts_theme_defaults(style_config)

        theme_name = str(chart_cfg.get("themeName") or derived_theme.get("themeName") or "report_default")
        palette = chart_cfg.get("palette") or derived_theme.get("palette") or DEFAULT_REPORT_STYLE["echartsTheme"]["palette"]
        if not isinstance(palette, list) or not palette:
            palette = DEFAULT_REPORT_STYLE["echartsTheme"]["palette"]
            self._warn("Invalid chart palette detected. Falling back to default palette.")

        axis_line_color = chart_cfg.get("axisLineColor") or derived_theme.get("axisLineColor")
        axis_label_color = chart_cfg.get("axisLabelColor") or derived_theme.get("axisLabelColor")
        split_line_color = chart_cfg.get("splitLineColor") or derived_theme.get("splitLineColor")

        theme = {
            "color": palette,
            "backgroundColor": chart_cfg.get("backgroundColor") or derived_theme.get("backgroundColor"),
            "textStyle": {
                "fontFamily": font_cfg.get("family"),
            },
            "title": {
                "textStyle": {
                    "color": chart_cfg.get("titleColor") or derived_theme.get("titleColor"),
                    "fontWeight": font_cfg.get("weightBold"),
                },
                "subtextStyle": {
                    "color": chart_cfg.get("subtitleColor") or derived_theme.get("subtitleColor"),
                },
            },
            "legend": {
                "textStyle": {
                    "color": chart_cfg.get("legendTextColor") or derived_theme.get("legendTextColor"),
                },
            },
            "toolbox": {
                "iconStyle": {
                    "borderColor": chart_cfg.get("toolboxIconBorderColor") or derived_theme.get("toolboxIconBorderColor"),
                },
            },
            "categoryAxis": {
                "axisLine": {
                    "lineStyle": {"color": axis_line_color},
                },
                "axisTick": {
                    "lineStyle": {"color": axis_line_color},
                },
                "axisLabel": {
                    "color": axis_label_color,
                },
                "splitLine": {
                    "lineStyle": {"color": [split_line_color]},
                },
            },
            "valueAxis": {
                "axisLine": {
                    "lineStyle": {"color": axis_line_color},
                },
                "axisTick": {
                    "lineStyle": {"color": axis_line_color},
                },
                "axisLabel": {
                    "color": axis_label_color},
                "splitLine": {
                    "lineStyle": {"color": [split_line_color]},
                },
            },
            "line": {
                "smooth": False,
                "symbol": "circle",
                "symbolSize": 7,
            },
            "bar": {
                "barMaxWidth": 28,
                "itemStyle": {
                    "borderRadius": [6, 6, 0, 0],
                },
            },
            "pie": {
                "label": {
                    "color": axis_label_color,
                },
                "labelLine": {
                    "lineStyle": {
                        "color": axis_line_color,
                    },
                },
            },
            "grid": chart_cfg.get("grid") or derived_theme.get("grid") or deepcopy(DEFAULT_REPORT_STYLE["echartsTheme"]["grid"]),
        }

        return {
            "theme_name": theme_name,
            "theme": theme,
        }

    def _normalize_component_schema(self, style_config: dict[str, Any]) -> None:
        """Backfill the newer report tree from older flat component branches when needed."""
        components = style_config.get("components")
        if not isinstance(components, dict):
            return

        existing_report = components.get("report") if isinstance(components.get("report"), dict) else {}

        def _first_non_none(*values: Any) -> Any:
            for value in values:
                if value is not None:
                    return value
            return None

        def _collapse_pdf_height_modes(current: Any) -> None:
            if not isinstance(current, dict):
                return

            height = current.get("height")
            if isinstance(height, dict):
                pdf_value = _first_non_none(
                    height.get("pdf"),
                    height.get("pdfCompact"),
                    height.get("pdfBase"),
                )
                if pdf_value is not None:
                    height["pdf"] = deepcopy(pdf_value)
                height.pop("pdfBase", None)
                height.pop("pdfCompact", None)

            for value in current.values():
                if isinstance(value, dict):
                    _collapse_pdf_height_modes(value)

        _collapse_pdf_height_modes(existing_report)
        self._ensure_palette_registry(style_config)
        self._ensure_theme_registry(style_config)
        self._sync_palette_tokens(style_config)
        self._apply_theme_refs(style_config)
        self._sync_legacy_color_tokens(style_config)

    def _validate_minimum_shape(self, style_config: dict[str, Any]) -> None:
        """Validate a minimal shape and normalize obviously invalid branches."""
        required_dict_sections = [
            "meta",
            "font",
            "color",
            "layout",
            "radius",
            "shadow",
            "spacing",
            "components",
            "echartsTheme",
        ]

        for section_name in required_dict_sections:
            value = style_config.get(section_name)
            if not isinstance(value, dict):
                style_config[section_name] = deepcopy(DEFAULT_REPORT_STYLE[section_name])
                self._warn(
                    f"Section '{section_name}' is invalid in {self._style_config_path}; default values were restored."
                )

        palette = style_config["echartsTheme"].get("palette")
        if not isinstance(palette, list) or not palette:
            style_config["echartsTheme"]["palette"] = deepcopy(
                DEFAULT_REPORT_STYLE["echartsTheme"]["palette"]
            )
            self._warn("Theme palette is missing or invalid; default palette was restored.")

    def _merge_defaults(self, defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
        """Deep-merge user overrides over defaults without dropping missing branches."""
        merged = deepcopy(defaults)

        for key, value in overrides.items():
            if key not in merged:
                merged[key] = deepcopy(value)
                continue

            default_value = merged[key]
            if isinstance(default_value, dict) and isinstance(value, dict):
                merged[key] = self._merge_defaults(default_value, value)
            elif value is not None:
                merged[key] = deepcopy(value)

        return merged

    def _flatten_css_variables(
        self,
        current: dict[str, Any],
        path: list[str] | None = None,
    ) -> list[str]:
        """Flatten nested dict tokens into CSS variable lines."""
        lines: list[str] = []
        current_path = path or []

        for key, value in current.items():
            next_path = [*current_path, self._to_kebab_case(key)]
            if isinstance(value, dict):
                lines.extend(self._flatten_css_variables(value, next_path))
                continue

            css_var_name = "--report-" + "-".join(next_path)
            lines.append(f"{css_var_name}: {value};")

        return lines

    def _derive_echarts_theme_defaults(self, style_config: dict[str, Any]) -> dict[str, Any]:
        """Derive a chart theme from semantic palette branches when available."""
        color_cfg = style_config.get("color", {}) if isinstance(style_config.get("color"), dict) else {}
        chart_cfg = color_cfg.get("chart", {}) if isinstance(color_cfg.get("chart"), dict) else {}

        defaults = deepcopy(DEFAULT_REPORT_STYLE["echartsTheme"])
        if isinstance(chart_cfg.get("palette"), list) and chart_cfg.get("palette"):
            defaults["palette"] = deepcopy(chart_cfg.get("palette"))

        key_map = {
            "background": "backgroundColor",
            "title": "titleColor",
            "subtitle": "subtitleColor",
            "legendText": "legendTextColor",
            "axisLine": "axisLineColor",
            "axisLabel": "axisLabelColor",
            "splitLine": "splitLineColor",
            "toolboxBorder": "toolboxIconBorderColor",
        }
        for source_key, target_key in key_map.items():
            if chart_cfg.get(source_key) is not None:
                defaults[target_key] = chart_cfg.get(source_key)

        return defaults

    def _ensure_palette_registry(self, style_config: dict[str, Any]) -> None:
        """Backfill the new short master palette from current semantic/report theme data."""
        palette_cfg = style_config.get("palette")
        if not isinstance(palette_cfg, dict):
            palette_cfg = {}
            style_config["palette"] = palette_cfg

        color_cfg = style_config.get("color") if isinstance(style_config.get("color"), dict) else {}
        text_cfg = color_cfg.get("text") if isinstance(color_cfg.get("text"), dict) else {}
        surface_cfg = color_cfg.get("surface") if isinstance(color_cfg.get("surface"), dict) else {}
        brand_cfg = color_cfg.get("brand") if isinstance(color_cfg.get("brand"), dict) else {}
        trend_cfg = color_cfg.get("trend") if isinstance(color_cfg.get("trend"), dict) else {}
        area_cfg = color_cfg.get("area") if isinstance(color_cfg.get("area"), dict) else {}

        components = style_config.get("components") if isinstance(style_config.get("components"), dict) else {}
        report_cfg = components.get("report") if isinstance(components.get("report"), dict) else {}
        section_cfg = report_cfg.get("section") if isinstance(report_cfg.get("section"), dict) else {}
        electric_cfg = section_cfg.get("electric") if isinstance(section_cfg.get("electric"), dict) else {}
        utility_cfg = section_cfg.get("utility") if isinstance(section_cfg.get("utility"), dict) else {}
        electric_card_theme = ((electric_cfg.get("card") or {}).get("theme") or {}) if isinstance(electric_cfg.get("card"), dict) else {}
        utility_card_theme = ((utility_cfg.get("card") or {}).get("theme") or {}) if isinstance(utility_cfg.get("card"), dict) else {}

        def _first_non_none(*values: Any) -> Any:
            for value in values:
                if value is not None:
                    return value
            return None

        palette_defaults = {
            "title": _first_non_none(text_cfg.get("heading"), color_cfg.get("textHeading"), "#0f2d45"),
            "textPrimary": _first_non_none(text_cfg.get("primary"), color_cfg.get("textPrimary"), "#223548"),
            "textMuted": _first_non_none(text_cfg.get("muted"), color_cfg.get("textMuted"), "#5f7387"),
            "neutral": _first_non_none(trend_cfg.get("neutral"), color_cfg.get("trendNeutral"), "#6c7f91"),
            "white": _first_non_none(text_cfg.get("inverse"), color_cfg.get("textInverse"), "#ffffff"),
            "page": _first_non_none(surface_cfg.get("page"), color_cfg.get("pageBackground"), "#edf3f8"),
            "brandPrimary": _first_non_none(brand_cfg.get("primary"), color_cfg.get("brandPrimary"), "#005496"),
            "previous": _first_non_none(text_cfg.get("previousValue"), brand_cfg.get("accent"), color_cfg.get("brandAccent"), "#703cd9"),
            "trendUp": _first_non_none(color_cfg.get("trendUp"), trend_cfg.get("up"), "#00c865"),
            "trendDown": _first_non_none(color_cfg.get("trendDown"), trend_cfg.get("down"), "#ff2301"),
            "trendNeutral": _first_non_none(color_cfg.get("trendNeutral"), trend_cfg.get("neutral"), "#6c7f91"),
            "areaDiode": _first_non_none(
                (area_cfg.get("diode") or {}).get("barColor") if isinstance(area_cfg.get("diode"), dict) else None,
                (electric_card_theme.get("diode") or {}).get("accent") if isinstance(electric_card_theme.get("diode"), dict) else None,
                "#005496",
            ),
            "areaIco": _first_non_none(
                (area_cfg.get("ico") or {}).get("barColor") if isinstance(area_cfg.get("ico"), dict) else None,
                (electric_card_theme.get("ico") or {}).get("accent") if isinstance(electric_card_theme.get("ico"), dict) else None,
                "#6f9a6d",
            ),
            "areaSakari": _first_non_none(
                (area_cfg.get("sakari") or {}).get("barColor") if isinstance(area_cfg.get("sakari"), dict) else None,
                (electric_card_theme.get("sakari") or {}).get("accent") if isinstance(electric_card_theme.get("sakari"), dict) else None,
                "#d09a45",
            ),
            "utilityWater": _first_non_none(
                (utility_card_theme.get("water") or {}).get("accent") if isinstance(utility_card_theme.get("water"), dict) else None,
                "#005496",
            ),
            "utilityCompressedAir": _first_non_none(
                (utility_card_theme.get("compressedAir") or {}).get("accent") if isinstance(utility_card_theme.get("compressedAir"), dict) else None,
                "#6f9a6d",
            ),
            "utilityChilledWater": _first_non_none(
                (utility_card_theme.get("chilledWater") or {}).get("accent") if isinstance(utility_card_theme.get("chilledWater"), dict) else None,
                "#5ca7a4",
            ),
            "utilitySteam": _first_non_none(
                (utility_card_theme.get("steam") or {}).get("accent") if isinstance(utility_card_theme.get("steam"), dict) else None,
                "#7a6da8",
            ),
        }

        for key, value in palette_defaults.items():
            if palette_cfg.get(key) is None and value is not None:
                palette_cfg[key] = deepcopy(value)

    def _ensure_theme_registry(self, style_config: dict[str, Any]) -> None:
        """Backfill the new theme registry with approved default theme refs."""
        themes_cfg = style_config.get("themes")
        if not isinstance(themes_cfg, dict):
            themes_cfg = {}
            style_config["themes"] = themes_cfg

        default_themes = {
            "titleHeader": {
                "default": {"seedRef": "brandPrimary", "mode": "headerShell"},
            },
            "sectionHeader": {
                "default": {"seedRef": "brandPrimary", "mode": "sectionHeader"},
            },
            "card": {
                "totalBrand": {"seedRef": "brandPrimary", "mode": "solidCard"},
                "areaDiode": {"seedRef": "areaDiode", "mode": "softCard"},
                "areaIco": {"seedRef": "areaIco", "mode": "softCard"},
                "areaSakari": {"seedRef": "areaSakari", "mode": "softCard"},
                "utilityWater": {"seedRef": "utilityWater", "mode": "softCard"},
                "utilityCompressedAir": {"seedRef": "utilityCompressedAir", "mode": "softCard"},
                "utilityChilledWater": {"seedRef": "utilityChilledWater", "mode": "softCard"},
                "utilitySteam": {"seedRef": "utilitySteam", "mode": "softCard"},
            },
            "chart": {
                "default": {"currentRef": "brandPrimary", "previousRef": "previous"},
                "areaDiode": {"currentRef": "areaDiode", "previousRef": "previous"},
                "areaIco": {"currentRef": "areaIco", "previousRef": "previous"},
                "areaSakari": {"currentRef": "areaSakari", "previousRef": "previous"},
                "utilityWater": {"currentRef": "utilityWater", "previousRef": "previous"},
                "utilityCompressedAir": {"currentRef": "utilityCompressedAir", "previousRef": "previous"},
                "utilityChilledWater": {"currentRef": "utilityChilledWater", "previousRef": "previous"},
                "utilitySteam": {"currentRef": "utilitySteam", "previousRef": "previous"},
            },
        }

        for group_key, default_group in default_themes.items():
            existing_group = themes_cfg.get(group_key)
            if not isinstance(existing_group, dict):
                themes_cfg[group_key] = deepcopy(default_group)
                continue

            for theme_key, default_theme in default_group.items():
                existing_theme = existing_group.get(theme_key)
                if not isinstance(existing_theme, dict):
                    existing_group[theme_key] = deepcopy(default_theme)
                    continue

                for prop_key, prop_value in default_theme.items():
                    existing_theme.setdefault(prop_key, deepcopy(prop_value))

    def _sync_palette_tokens(self, style_config: dict[str, Any]) -> None:
        """Mirror the new short palette into the current semantic color tree for safe migration."""
        palette_cfg = style_config.get("palette")
        color_cfg = style_config.get("color")
        if not isinstance(palette_cfg, dict) or not isinstance(color_cfg, dict):
            return

        text_cfg = color_cfg.get("text") if isinstance(color_cfg.get("text"), dict) else {}
        surface_cfg = color_cfg.get("surface") if isinstance(color_cfg.get("surface"), dict) else {}
        brand_cfg = color_cfg.get("brand") if isinstance(color_cfg.get("brand"), dict) else {}
        trend_cfg = color_cfg.get("trend") if isinstance(color_cfg.get("trend"), dict) else {}
        chart_cfg = color_cfg.get("chart") if isinstance(color_cfg.get("chart"), dict) else {}
        chart_series_cfg = chart_cfg.get("series") if isinstance(chart_cfg.get("series"), dict) else {}
        area_cfg = color_cfg.get("area") if isinstance(color_cfg.get("area"), dict) else {}

        text_cfg["heading"] = palette_cfg.get("title", text_cfg.get("heading"))
        text_cfg["primary"] = palette_cfg.get("textPrimary", text_cfg.get("primary"))
        text_cfg["muted"] = palette_cfg.get("textMuted", text_cfg.get("muted"))
        text_cfg["inverse"] = palette_cfg.get("white", text_cfg.get("inverse"))
        text_cfg["previousValue"] = palette_cfg.get("previous", text_cfg.get("previousValue"))
        color_cfg["text"] = text_cfg

        surface_cfg["page"] = palette_cfg.get("page", surface_cfg.get("page"))
        color_cfg["surface"] = surface_cfg

        brand_cfg["primary"] = palette_cfg.get("brandPrimary", brand_cfg.get("primary"))
        brand_cfg["accent"] = palette_cfg.get("previous", brand_cfg.get("accent"))
        color_cfg["brand"] = brand_cfg

        trend_cfg["up"] = palette_cfg.get("trendUp", trend_cfg.get("up"))
        trend_cfg["down"] = palette_cfg.get("trendDown", trend_cfg.get("down"))
        trend_cfg["neutral"] = palette_cfg.get("trendNeutral", trend_cfg.get("neutral"))
        color_cfg["trend"] = trend_cfg

        if isinstance(chart_series_cfg, dict):
            chart_series_cfg["current"] = palette_cfg.get("brandPrimary", chart_series_cfg.get("current"))
            chart_series_cfg["previous"] = palette_cfg.get("previous", chart_series_cfg.get("previous"))
            chart_cfg["series"] = chart_series_cfg
            color_cfg["chart"] = chart_cfg

        for area_key, palette_key in (("diode", "areaDiode"), ("ico", "areaIco"), ("sakari", "areaSakari")):
            area_node = area_cfg.get(area_key) if isinstance(area_cfg.get(area_key), dict) else {}
            area_node["barColor"] = palette_cfg.get(palette_key, area_node.get("barColor"))
            area_cfg[area_key] = area_node
        color_cfg["area"] = area_cfg

    def _resolve_theme_ref(self, style_config: dict[str, Any], theme_ref: str) -> dict[str, Any]:
        """Resolve a dotted theme ref such as `card.totalBrand` against `reportStyle.themes`."""
        if not theme_ref or not isinstance(theme_ref, str) or "." not in theme_ref:
            return {}

        themes_cfg = style_config.get("themes") if isinstance(style_config.get("themes"), dict) else {}
        group_key, theme_key = theme_ref.split(".", 1)
        group_cfg = themes_cfg.get(group_key) if isinstance(themes_cfg.get(group_key), dict) else {}
        theme_cfg = group_cfg.get(theme_key)
        return deepcopy(theme_cfg) if isinstance(theme_cfg, dict) else {}

    def _parse_hex_color(self, value: str) -> tuple[int, int, int] | None:
        """Parse a #RRGGBB or #RGB color string into an RGB tuple."""
        if not isinstance(value, str):
            return None
        raw = value.strip()
        if not raw.startswith("#"):
            return None
        raw = raw[1:]
        if len(raw) == 3:
            raw = "".join(ch * 2 for ch in raw)
        if len(raw) != 6:
            return None
        try:
            return tuple(int(raw[idx:idx + 2], 16) for idx in (0, 2, 4))
        except ValueError:
            return None

    def _to_hex_color(self, rgb: tuple[int, int, int] | None, fallback: str = "#000000") -> str:
        """Convert an RGB tuple back into #RRGGBB form."""
        if rgb is None:
            return fallback
        return "#" + "".join(f"{max(0, min(255, channel)):02x}" for channel in rgb)

    def _mix_hex_colors(self, base: str, other: str, other_ratio: float) -> str:
        """Mix two hex colors using `other_ratio` as the contribution of `other`."""
        base_rgb = self._parse_hex_color(base)
        other_rgb = self._parse_hex_color(other)
        if base_rgb is None or other_rgb is None:
            return base if base_rgb is not None else other
        ratio = max(0.0, min(1.0, float(other_ratio)))
        mixed = tuple(round(base_rgb[idx] * (1.0 - ratio) + other_rgb[idx] * ratio) for idx in range(3))
        return self._to_hex_color(mixed, fallback=base)

    def _hex_to_rgba(self, base: str, alpha: float) -> str:
        """Convert a hex color into an rgba(...) string."""
        rgb = self._parse_hex_color(base)
        if rgb is None:
            return base
        alpha_value = max(0.0, min(1.0, float(alpha)))
        alpha_text = f"{alpha_value:.2f}".rstrip("0").rstrip(".")
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha_text})"

    def _derive_theme_mode_tokens(self, style_config: dict[str, Any], theme_cfg: dict[str, Any]) -> dict[str, Any]:
        """Derive pilot component tokens from a theme registry entry."""
        palette_cfg = style_config.get("palette") if isinstance(style_config.get("palette"), dict) else {}
        seed_ref = theme_cfg.get("seedRef")
        seed = palette_cfg.get(seed_ref) if isinstance(seed_ref, str) else None
        if not isinstance(seed, str):
            return {}

        mode = theme_cfg.get("mode")
        title = palette_cfg.get("title", "#0f2d45")
        text_primary = palette_cfg.get("textPrimary", "#223548")
        text_muted = palette_cfg.get("textMuted", "#5f7387")
        neutral = palette_cfg.get("neutral", "#6c7f91")
        white = palette_cfg.get("white", "#ffffff")
        previous = palette_cfg.get("previous", "#703cd9")
        soft_bg = self._mix_hex_colors(seed, white, 0.93)
        soft_border = self._mix_hex_colors(seed, white, 0.75)
        strong_border = self._mix_hex_colors(seed, white, 0.35)
        seed_light = self._mix_hex_colors(seed, white, 0.18)

        if mode == "headerShell":
            return {
                "background": white,
                "borderColor": self._mix_hex_colors(seed, white, 0.80),
                "shadow": f"0 12px 28px {self._hex_to_rgba(seed, 0.12)}",
                "overlayGradient": (
                    "linear-gradient(90deg, rgba(255,255,255,0.04) 0%, "
                    "rgba(255,255,255,0.02) 36%, "
                    f"{self._hex_to_rgba(seed, 0.16)} 100%)"
                ),
                "dividerColor": self._hex_to_rgba(seed, 0.16),
                "dateChipBackground": self._hex_to_rgba(white, 0.96),
                "dateChipBorderColor": self._mix_hex_colors(seed, white, 0.80),
                "dateChipTextColor": title,
                "dateChipMutedColor": text_muted,
                "dateChipIconColor": seed,
                "dateChipShadow": f"inset 0 0 0 1px {self._hex_to_rgba(seed, 0.08)}",
                "accentBorderColor": seed,
            }

        if mode == "sectionHeader":
            return {
                "background": soft_bg,
                "borderColor": soft_border,
                "accentColor": seed,
                "titleColor": title,
                "subtitleColor": text_muted,
                "dateChipBackground": self._hex_to_rgba(white, 0.94),
                "dateChipBorderColor": self._mix_hex_colors(seed, white, 0.80),
                "dateChipTextColor": title,
                "dateChipMutedColor": text_muted,
                "dateChipIconColor": seed,
                "dateChipShadow": f"inset 0 0 0 1px {self._hex_to_rgba(seed, 0.08)}",
                "accentBorderColor": seed,
            }

        if mode == "solidCard":
            return {
                "accent": seed,
                "borderColor": strong_border,
                "surface": f"linear-gradient(135deg, {seed} 0%, {seed_light} 100%)",
                "shadow": f"0 16px 28px {self._hex_to_rgba(seed, 0.22)}",
                "titleColor": white,
                "copyColor": self._hex_to_rgba(white, 0.84),
                "currentColor": white,
                "previousColor": previous,
                "noteColor": self._hex_to_rgba(white, 0.88),
                "iconBackground": white,
                "iconColor": seed,
                "primaryColor": white,
                "primaryUnitColor": self._hex_to_rgba(white, 0.94),
                "compareBackground": self._hex_to_rgba(white, 0.98),
                "compareBorderColor": self._hex_to_rgba(soft_border, 0.96),
                "compareDividerColor": self._hex_to_rgba(self._mix_hex_colors(seed, white, 0.82), 0.92),
            }

        if mode == "softCard":
            return {
                "accent": seed,
                "borderColor": soft_border,
                "surface": f"linear-gradient(135deg, {self._hex_to_rgba(seed, 0.12)} 0%, {self._hex_to_rgba(white, 0.94)} 56%, {self._hex_to_rgba(white, 0.99)} 100%)",
                "titleColor": title,
                "copyColor": text_muted,
                "currentColor": seed,
                "previousColor": previous,
                "noteColor": neutral,
                "iconBackground": seed,
                "iconColor": white,
                "primaryColor": seed,
                "primaryUnitColor": title,
                "compareBackground": self._hex_to_rgba(white, 0.94),
                "compareBorderColor": self._hex_to_rgba(soft_border, 0.95),
                "compareDividerColor": self._hex_to_rgba(self._mix_hex_colors(seed, white, 0.82), 0.95),
            }

        return {}

    def _apply_theme_refs(self, style_config: dict[str, Any]) -> None:
        """Resolve approved pilot `themeRef` branches into concrete tokens before CSS flattening."""
        components = style_config.get("components") if isinstance(style_config.get("components"), dict) else {}
        report_cfg = components.get("report") if isinstance(components.get("report"), dict) else {}
        section_cfg = report_cfg.get("section") if isinstance(report_cfg.get("section"), dict) else {}

        pilot_nodes = []
        title_header = report_cfg.get("titleHeader") if isinstance(report_cfg.get("titleHeader"), dict) else {}
        title_shell = title_header.get("shell") if isinstance(title_header.get("shell"), dict) else None
        if isinstance(title_shell, dict):
            pilot_nodes.append(title_shell)

        common_cfg = section_cfg.get("common") if isinstance(section_cfg.get("common"), dict) else {}
        common_header = common_cfg.get("header") if isinstance(common_cfg.get("header"), dict) else None
        if isinstance(common_header, dict):
            pilot_nodes.append(common_header)

        electric_cfg = section_cfg.get("electric") if isinstance(section_cfg.get("electric"), dict) else {}
        electric_card_cfg = electric_cfg.get("card") if isinstance(electric_cfg.get("card"), dict) else {}
        electric_theme_cfg = electric_card_cfg.get("theme") if isinstance(electric_card_cfg.get("theme"), dict) else {}
        electric_total = electric_theme_cfg.get("total") if isinstance(electric_theme_cfg.get("total"), dict) else None
        if isinstance(electric_total, dict):
            pilot_nodes.append(electric_total)

        for node in pilot_nodes:
            theme_ref = node.get("themeRef")
            if not isinstance(theme_ref, str) or not theme_ref:
                continue
            theme_cfg = self._resolve_theme_ref(style_config, theme_ref)
            if not theme_cfg:
                continue
            derived_tokens = self._derive_theme_mode_tokens(style_config, theme_cfg)
            if not derived_tokens:
                continue
            for key, value in derived_tokens.items():
                node[key] = deepcopy(value)

    def _sync_legacy_color_tokens(self, style_config: dict[str, Any]) -> None:
        """Keep flat legacy color keys aligned with semantic palette branches."""
        color_cfg = style_config.get("color")
        if not isinstance(color_cfg, dict):
            return

        surface_cfg = color_cfg.get("surface") if isinstance(color_cfg.get("surface"), dict) else {}
        text_cfg = color_cfg.get("text") if isinstance(color_cfg.get("text"), dict) else {}
        border_cfg = color_cfg.get("border") if isinstance(color_cfg.get("border"), dict) else {}
        brand_cfg = color_cfg.get("brand") if isinstance(color_cfg.get("brand"), dict) else {}
        trend_cfg = color_cfg.get("trend") if isinstance(color_cfg.get("trend"), dict) else {}
        status_cfg = color_cfg.get("status") if isinstance(color_cfg.get("status"), dict) else {}

        sync_map = {
            "pageBackground": surface_cfg.get("page"),
            "cardBackground": surface_cfg.get("card"),
            "headerBackground": surface_cfg.get("header"),
            "headerBackgroundStrong": surface_cfg.get("headerStrong"),
            "tableStripeBackground": surface_cfg.get("tableStripe"),
            "tableHeaderBackground": surface_cfg.get("tableHeader"),
            "textPrimary": text_cfg.get("primary"),
            "textHeading": text_cfg.get("heading"),
            "textMuted": text_cfg.get("muted"),
            "textSubtle": text_cfg.get("subtle"),
            "textInverse": text_cfg.get("inverse"),
            "borderDefault": border_cfg.get("default"),
            "borderSoft": border_cfg.get("soft"),
            "borderRow": border_cfg.get("row"),
            "brandPrimary": brand_cfg.get("primary"),
            "brandAccent": brand_cfg.get("accent"),
            "trendUp": trend_cfg.get("up"),
            "trendDown": trend_cfg.get("down"),
            "trendNeutral": trend_cfg.get("neutral"),
        }
        for key, value in sync_map.items():
            if value is not None:
                color_cfg[key] = value

        for status_name, legacy_text_key, legacy_bg_key in (
            ("success", "statusSuccess", "statusSuccessBackground"),
            ("warning", "statusWarning", "statusWarningBackground"),
            ("danger", "statusDanger", "statusDangerBackground"),
            ("neutral", "statusNeutral", "statusNeutralBackground"),
        ):
            status_node = status_cfg.get(status_name) if isinstance(status_cfg.get(status_name), dict) else {}
            text_value = status_node.get("text")
            background_value = status_node.get("background")
            if text_value is not None:
                color_cfg[legacy_text_key] = text_value
            if background_value is not None:
                color_cfg[legacy_bg_key] = background_value

    def _build_compatibility_aliases(self, style_config: dict[str, Any]) -> list[str]:
        """Emit bridge variables so rollout can be gradual in existing CSS assets."""
        aliases: list[str] = []

        report_cfg = (style_config.get("components", {}) or {}).get("report", {})
        section_cfg = report_cfg.get("section", {}) if isinstance(report_cfg, dict) else {}
        common_cfg = section_cfg.get("common", {}) if isinstance(section_cfg, dict) else {}
        if isinstance(common_cfg.get("header"), dict):
            aliases.extend([
                "--report-components-section-header-title-color: var(--report-components-report-section-common-header-title-color);",
                "--report-components-section-header-subtitle-color: var(--report-components-report-section-common-header-subtitle-color);",
                "--report-components-section-header-border-color: var(--report-components-report-section-common-header-border-color);",
                "--report-components-section-header-accent-color: var(--report-components-report-section-common-header-accent-color);",
            ])

        return aliases

    def _to_kebab_case(self, value: str) -> str:
        """Convert camelCase or mixedCase text to kebab-case for CSS variable names."""
        with_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", str(value or ""))
        return with_boundaries.replace("_", "-").lower()

    def _warn(self, message: str) -> None:
        """Record and log a non-fatal warning."""
        self._warnings.append(message)
        logger.warning(message)
