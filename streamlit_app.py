import ee
import geemap.foliumap as geemap
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("A National Dataset of Surface Depressions")

st.sidebar.info("Contact: [Qiusheng Wu](https://wetlands.io)")

tab1, tab2 = st.tabs(["Selection", "Results"])

with tab1:

    col1, col2 = st.columns([4, 1])

    Map = geemap.Map(
        center=[40, -100],
        zoom=4,
        search_control=False,
        scale_control=True,
        add_google_map=False,
    )

    Map.add_basemap("HYBRID")
    Map.add_basemap("ROADMAP")

    if "map" not in st.session_state:
        st.session_state.map = None
    if "lon" not in st.session_state:
        st.session_state.lon = -100
    if "lat" not in st.session_state:
        st.session_state.lat = 40

    ned = ee.Image("USGS/3DEP/10m")
    hillshade = ee.Terrain.hillshade(ned)
    Map.addLayer(ned, {"min": 0, "max": 4000, "palette": "terrain"}, "NED (10-m)")
    Map.addLayer(hillshade, {}, "Hillshade")

    conus = ee.Geometry.BBox(-127.18, 19.39, -62.75, 51.29)
    huc8 = ee.FeatureCollection("USGS/WBD/2017/HUC08").filterBounds(conus)
    style = {"color": "00000088", "fillColor": "00000000", "width": 1}
    Map.addLayer(huc8.style(**style), {}, "NHD-HUC8")

    pipestem_hu8 = ee.FeatureCollection("users/giswqs/Pipestem/Pipestem_HUC8")
    Map.addLayer(
        pipestem_hu8.style(
            **{"color": "ffff00ff", "fillColor": "00000000", "width": 2}
        ),
        {},
        "Pipestem HUC8",
    )

    if "map" in st.session_state and st.session_state.map is not None:
        last_clicked = st.session_state.map.last_clicked
        lng = last_clicked["lng"]
        lat = last_clicked["lat"]
        roi = ee.Geometry.Point([lng, lat])

    with col1:
        placeholder = st.empty()
        with placeholder.container():
            output = st_folium(Map, key="map", height=650, width=1400)

    with col2:

        st.info(
            "Click on the map to select a watershed. Then switch to the **Results** tab to see the results."
        )

        if output is not None and output["last_clicked"] is not None:
            lon_default = output["last_clicked"]["lng"]
            lat_default = output["last_clicked"]["lat"]

        else:
            lon_default = -100.0
            lat_default = 40.0

        st.write("Clicked location:")
        lon = st.number_input("Longitude", value=lon_default, key="lon")
        lat = st.number_input("Latitude", value=lat_default, key="lat")

        roi = ee.Geometry.Point([lon, lat])
        # Map.addLayer(huc8.filterBounds(roi), {}, "Selected Point")

        # button = st.button("Submit")
        # if button:
        #     placeholder.empty()

        #     with placeholder.container():
        #         output = st_folium(Map, height=650, width=1400)

with tab2:

    try:
        selected = huc8.filterBounds(roi)
        huc_id = selected.first().get("huc8").getInfo()
        st.dataframe(geemap.ee_to_df(selected))

        Map = geemap.Map()
        Map.add_basemap("HYBRID")

        hillshade_clip = hillshade.clipToCollection(selected)
        Map.addLayer(hillshade_clip, {}, "Hillshade")

        if huc_id == "10160002":

            pipestem = ee.FeatureCollection("users/giswqs/Pipestem/Pipestem_HUC10")
            lidar = ee.Image("users/giswqs/Pipestem/lidar_3m")
            intensity = ee.Image("users/giswqs/Pipestem/intensity")
            hillshade = ee.Terrain.hillshade(lidar)
            flowpaths = ee.FeatureCollection("users/giswqs/Pipestem/flow_paths")
            depressions_lidar = ee.FeatureCollection(
                "users/giswqs/Pipestem/depressions"
            )
            flow_from = ee.FeatureCollection("users/giswqs/Pipestem/flow_from")
            flow_to = ee.FeatureCollection("users/giswqs/Pipestem/flow_to")
            catchments = ee.FeatureCollection("users/giswqs/Pipestem/catchments")
            nwi = ee.FeatureCollection("users/giswqs/Pipestem/NWI")

            empty = ee.Image().byte()

            Map.setCenter(-99.09526, 47.099772, 15)

            Map.addLayer(
                intensity, {"min": 0, "max": 255}, "LiDAR Intensity", False
            )
            Map.addLayer(lidar, {"min": 400, "max": 700}, "LiDAR DEM", False)
            Map.addLayer(hillshade, {}, "DEM Hillshade")
            Map.addLayer(
                empty.paint(catchments, 0, 2),
                {"palette": "pink"},
                "Catchments",
                False,
            )
            Map.addLayer(
                depressions_lidar.style(
                    **{"color": "00000000", "fillColor": "0000ff50"}
                ),
                {},
                "Depressions (1-m)",
            )
            # Map.addLayer(nwi, {}, "NWI", False)
            Map.addLayer(
                empty.paint(flowpaths, 0, 2), {"palette": "blue"}, "Flow path"
            )
            Map.addLayer(flow_from, {"color": "red"}, "Water outlet")
            Map.addLayer(flow_to, {"color": "green"}, "Water inlet")
            # Map.addLayer(empty.paint(pipestem, 0, 2), {}, "Pipestem HUC-10")

        Map.addLayer(
            selected.style(**{"color": "ff0000ff", "fillColor": "00000000"}),
            {},
            "Selected Watershed",
        )
        depression_id = f"users/giswqs/depressions/{huc_id}"
        depressions = ee.FeatureCollection(depression_id)
        nwi_id = f"users/giswqs/NWI-HU8/HU8_{huc_id}_Wetlands"
        nwi = ee.FeatureCollection(nwi_id)

        names = [
            "Freshwater Forested/Shrub Wetland",
            "Freshwater Emergent Wetland",
            "Freshwater Pond",
            "Estuarine and Marine Wetland",
            "Riverine",
            "Lake",
            "Estuarine and Marine Deepwater",
            "Other",
        ]

        colors = [
            "#008837",
            "#7FC31C",
            "#688CC0",
            "#66C2A5",
            "#0190BF",
            "#13007C",
            "#007C88",
            "#B28653",
        ]
        color_dict = ee.Dictionary(dict(zip(names, colors)))

        nwi_fc = nwi.map(
            lambda f: f.set(
                {
                    "style": {
                        "width": 1,
                        "color": "00000088",
                        "fillColor": ee.String(
                            color_dict.get(f.get("WETLAND_TY"))
                        ).cat("99"),
                    }
                }
            )
        )
        Map.addLayer(nwi_fc.style(**{"styleProperty": "style"}), {}, "NWI Wetlands")
        Map.add_legend(title="NWI Wetland Type", builtin_legend="NWI")

        # Map.addLayer(nwi, {}, "NWI Wetlands")
        Map.addLayer(depressions, {}, "Depressions (10-m)")
        Map.center_object(selected, 9)
        Map.to_streamlit()

        huc_area = selected.first().get("areasqkm")
        st.write(f"HUC8 Area: {huc_area.getInfo()} km2")
        st.dataframe(geemap.ee_to_df(ee.FeatureCollection([depressions.first()])))
        depression_area = ee.Number(depressions.aggregate_array("area")).divide(1e6)
        depression_volume = ee.Number(depressions.aggregate_array("volume")).divide(
            1e9
        )
        # depression_count = ee.Number(depressions.size())

        # result_dict = ee.Dictionary(
        #     {
        #         "HUC8 Area (sqkm)": huc_area,
        #         "Depression Count": depression_count,
        #         "Depression Area (sqkm)": depression_area,
        #         "Depression Volume (km3)": depression_volume,
        #     }
        # )
        # st.write(result_dict.getInfo())

    except Exception as e:
        st.error(e)
