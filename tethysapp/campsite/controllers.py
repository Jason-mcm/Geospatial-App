import json
from tethys_sdk.gizmos import *
from django.shortcuts import render
from tethys_sdk.gizmos import MapView, MVDraw, MVView, MVLayer, MVLegendClass, Button
from django.urls import reverse_lazy
from tethys_sdk.layouts import MapLayout
from tethys_sdk.routing import controller
from .app import Campsite as app


@controller
def home(request):
    """
    Controller for the app home page.
    """
    context = {}
    return render(request, 'campsite/home.html', context)


@controller(url='campsite/draw')
def draw(request):
    """
    Controller for the Add Dam page.
    """
    # Define drawing options
    drawing_options = MVDraw(
        controls=['Modify', 'Delete', 'Move', 'Point', 'LineString', 'Polygon', 'Box', 'Pan'],
        output_format='GeoJSON',
        line_color='#ad1b13',
        fill_color='rgba(173, 27, 19,0.2)',
        point_color='#ad1b13'
    )

    view_options = MVView(
        projection='EPSG:4326',
        center=[-100, 40],
        zoom=3.5,
        maxZoom=18,
        minZoom=2
    )

    # Define GeoJSON layer
    geojson_object = {
        'type': 'FeatureCollection',
        'crs': {
            'type': 'name',
            'properties': {
                'name': 'EPSG:3857'
            }
        },
        'features': [
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [0, 0]
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [[4e6, -2e6], [8e6, 2e6]]
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[[-5e6, -1e6], [-4e6, 1e6], [-3e6, -1e6]]]
                }
            }
        ]
    }

    style = {'ol.style.Style': {
        'stroke': {'ol.style.Stroke': {
            'color': 'blue',
            'width': 2
        }},
        'fill': {'ol.style.Fill': {
            'color': 'green'
        }},
        'image': {'ol.style.Circle': {
            'radius': 10,
            'fill': None,
            'stroke': {'ol.style.Stroke': {
                'color': 'red',
                'width': 2
            }}
        }}
    }}

    geojson_layer = MVLayer(
        source='GeoJSON',
        options=geojson_object,
        layer_options={'style': style},
        legend_title='Test GeoJSON',
        legend_extent=[-46.7, -48.5, 74, 59],
        legend_classes=[
            MVLegendClass('polygon', 'Polygons', fill='green', stroke='blue'),
            MVLegendClass('line', 'Lines', stroke='blue')
        ]
    )

    # Define map view options
    map_options = MapView(
        height='100%',
        width='100%',
        controls=['ZoomSlider', 'Rotate', 'FullScreen',
                  {'MousePosition': {'projection': 'EPSG:4326'}},
                  {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-130, 22, -65, 54]}}],
        layers=[geojson_layer],
        view=view_options,
        draw=drawing_options,
        legend=True,
    )

    context = {'map_options': map_options}
    return render(request, 'campsite/draw.html', context)


@controller(
    name="map",
    url="campsite/map"
)
class Campsite(MapLayout):
    app = app
    base_template = 'campsite/base.html'
    back_url = reverse_lazy('campsite:home')
    map_title = 'Map View'
    map_subtitle = 'Find the perfect campsite!'
    basemaps = [
        'OpenStreetMap',
        'ESRI',
        'Stamen',
        {'Stamen': {'layer': 'toner', 'control_label': 'Black and White'}},
    ]
    default_map_extent = [-65.69, 23.81, -129.17, 49.38]  # CONUS bbox
    max_zoom = 16
    min_zoom = 2
    show_properties_popup = True
    plot_slide_sheet = True

    def compose_layers(self, request, map_view, *args, **kwargs):
        """
        Add layers to the MapLayout and create associated layer group objects.
        """
        # Load GeoJSON From File
        us_states_path = 'tethysapp/campsite/us-states.json'
        with open(us_states_path) as gj:
            us_states_geojson = json.loads(gj.read())

        # GeoJSON Layer
        us_states_layer = self.build_geojson_layer(
            geojson=us_states_geojson,
            layer_name='us-states',
            layer_title='U.S. States',
            layer_variable='reference',
            visible=True,
            selectable=True,
            plottable=True
        )
        map_view.layers.append(us_states_layer)

        # # Load GeoJSON From File
        # lakes_path = 'tethysapp/campsite/Utah_Lakes_NHD.geojson'
        # with open(lakes_path) as gj:
        #     lakes_geojson = json.loads(gj.read())
        #
        # # GeoJSON Layer
        # lakes_layer = self.build_geojson_layer(
        #     geojson=lakes_geojson,
        #     layer_name='lakes',
        #     layer_title='Utah Lakes',
        #     layer_variable='lakes',
        #     visible=False,
        #     selectable=True,
        #     plottable=True
        # )
        # map_view.layers.append(lakes_layer)

        counties = self.build_wms_layer(
            endpoint='http://localhost:8181/geoserver/wms',
            server_type='geoserver',
            layer_name='campsite_app:Counties',
            layer_title='Utah Counties',
            layer_variable='c',
            visible=True,  # Set to False if the layer should be hidden initially
        )
        map_view.layers.append(counties)

        precip_layer = self.build_arc_gis_layer(
            endpoint='https://mapservices.weather.noaa.gov/raster/rest/services/obs/rfc_qpe/MapServer',
            layer_name='25',  # ArcGIS MapServer Layer ID
            layer_title='Precipitation Last 24 Hours (inches)',
            layer_variable='precipitation',
            visible=False,
            extent=[-65.69, 23.81, -129.17, 49.38],  # CONUS bbox
        )

        # Add layer to map
        map_view.layers.append(precip_layer)

        # Add layer to layer group
        layer_groups = [
            self.build_layer_group(
                id='usa-layer-group',
                display_name='United States',
                layer_control='checkbox',  # 'radio' or 'check'
                layers=[
                    us_states_layer, counties, precip_layer
                ],
            ),
        ]

        return layer_groups

    @classmethod
    def get_vector_style_map(cls):
        return {
            'Point': {'ol.style.Style': {
                'image': {'ol.style.Circle': {
                    'radius': 5,
                    'fill': {'ol.style.Fill': {
                        'color': 'red',
                    }},
                    'stroke': {'ol.style.Stroke': {
                        'color': 'red',
                        'width': 2
                    }}
                }}
            }},
            'LineString': {'ol.style.Style': {
                'stroke': {'ol.style.Stroke': {
                    'color': 'green',
                    'width': 3
                }}
            }},
            'MultiPolygon': {'ol.style.Style': {
                'stroke': {'ol.style.Stroke': {
                    'color': 'green',
                    'width': 3
                }},
                'fill': {'ol.style.Fill': {
                    'color': 'rgba(0, 255, 0, 0.1)'
                }}
            }},
            'Polygon': {'ol.style.Style': {
                'stroke': {'ol.style.Stroke': {
                    'color': 'green',
                    'width': 3
                }},
                'fill': {'ol.style.Fill': {
                    'color': 'rgba(0, 255, 0, 0.1)'
                }}
            }},
        }