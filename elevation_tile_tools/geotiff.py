import datetime
import os
import shutil

from osgeo import gdal, osr


class GeoTiff:
    def __init__(self, output_path):
        self.output_path = output_path

    # アレイと座標、ピクセルサイズ、グリッドサイズからGeoTiffを作成
    def write_geotiff(
        self,
        array,
        lower_left_lon,
        upper_right_lat,
        pixel_size_x,
        pixel_size_y,
        xlen,
        ylen,
    ):
        # 「左下経度・東西解像度・回転（０で南北方向）・右上緯度・回転（０で南北方向）・南北解像度（北南方向であれば負）」
        geotransform = [
            lower_left_lon,
            pixel_size_x,
            0,
            upper_right_lat,
            0,
            pixel_size_y,
        ]

        merge_tiff_file = "output.tif"
        tiffFile = os.path.join(self.output_path, merge_tiff_file)

        # ドライバーの作成
        driver = gdal.GetDriverByName("GTiff")
        # ドライバーに対して「保存するファイルのパス・グリットセル数・バンド数・ラスターの種類・ドライバー固有のオプション」を指定してファイルを作成
        dst_ds = driver.Create(tiffFile, xlen, ylen, 1, gdal.GDT_Float32)
        # geotransformをセット
        dst_ds.SetGeoTransform(geotransform)

        # 作成したラスターの第一バンドを取得
        rband = dst_ds.GetRasterBand(1)
        # 第一バンドにアレイをセット
        rband.WriteArray(array)
        # nodataの設定
        rband.SetNoDataValue(-9999)

        # EPSGコードを引数にとる前処理？
        ref = osr.SpatialReference()
        # EPSGコードを引数にとる
        ref.ImportFromEPSG(3857)
        # ラスターに投影法の情報を入れる
        dst_ds.SetProjection(ref.ExportToWkt())

        # ディスクへの書き出し
        dst_ds.FlushCache()

    # 再投影
    def reprojection(self, src_epsg, output_epsg):
        src_path = os.path.join(self.output_path, "output.tif")
        # warp前後で同名のファイルを指定できないため、一時ファイルを作成する
        now = datetime.datetime.now()
        tmp_filename = f"tmp_{now.strftime('%Y%m%d_%H%M%S')}.tif"
        warped_path = os.path.join(self.output_path, tmp_filename)
        shutil.copy2(src_path, warped_path)

        resampled_ras = gdal.Warp(
            warped_path,
            src_path,
            srcSRS=src_epsg,
            dstSRS=output_epsg,
            resampleAlg="near"
        )
        resampled_ras.FlushCache()
        del resampled_ras

        os.remove(src_path)
        os.rename(warped_path, src_path)

