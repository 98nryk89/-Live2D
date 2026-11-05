# 無価値価値 Webカメラ版0.4.0

利用者指定：目の形が崩壊しているため新しい3段階差分を使う。口はおおよそOKなので保持。かしげは左右とも5度。熊の耳の一部が髪につながる所属を修正。

## 新しい素材
アーカイブ2の2枚の原本をcharacter_materials/mukachi_kachi/revision4_originalsへ変更せず保存。
2172×724のシートは724×724ずつの開・半開・閉の順と確認済み。1350×1165のもう1枚は熊・装飾を外した背面資料。
tools/prepare_revision4.pyで髪の特徴点に基づく全体の位置・倍率だけを合わせる。各段階で30〜38点、背面資料54点を採用、特徴点誤差中央値は約0.49〜0.65px。SHA、切出し範囲、アフィン行列はprojects/mukachi_kachi/revision4_materials.jsonに保存。

## 変更
- 目：40段階の目・肌のリマップ、生成した中間瞼を廃止。提供された開・半開・閉を、局所的な変形なしで使用。眼球を潰さず、肌を塗り直さない。目の周囲の境界は1px程度だけなじませ、内側は不透明にして元の眼球が透けないようにする。段階の往復を抑えるヒステリシスを追加。画像同士を半透明で重ねた中間形状は作らない。
- 口：0.3.0の98口レイヤーについて、埋込PNGとメッシュが完全一致することを確認。口の形・傾き・開閉処理は変更していない。
- かしげ：入力とリグの上限を左右とも5度へ統一。
- 肩の熊：熊全体をcompanionとして独立させ、耳の付け根・先端・輪郭を熊側へ戻す。従来はy329〜345の頭境界の斜め補間が熊の耳先を拾っていた。髪側に熊の耳の画素を残さない。
- 熊の背面：提供された下絵の髪を、熊の裏の必要領域だけhair_behind_companionとして頭に追従させる。熊は髪より前に描画し、肩に固定する。資料全体へ差し替えたり、衣装・装飾を描き直したりしない。キャラ頭上の熊耳は従来どおり頭に固定。

## 検査
- 新版28項目：提供3画像から左右のRGBがそのまま組み込まれること、目の内側の不透明性、生成された40段階が残っていないこと、口98レイヤーの完全一致、熊耳の所属、実レンダラでの3段階切替、±5度の熊耳の固定、両方向の制限、配布ZIPのHTML一致、JSエラーなし。
- 従来の口・体・装飾の検査107項目と、顔・首の幾何検査14項目を新しい±5度に合わせて通過。配布の疑似カメラ7項目も通過。
- docs/verification/repair_0.4.0/authored_blinks_rendered.jpgで3状態を拡大確認。左右かしげのsplit_tilt_-5.png、split_tilt_5.pngで熊の耳と髪の動きを目視確認。

実Macのカメラ/OBSの見え方は未確認。滑らかさを優先して未提供の形を生成することはせず、今回は指定された3枚の形を優先する。

## 再生成
requirements-validated.txtを導入したPythonで、tools/prepare_character.py、tools/prepare_revision4.py、tools/build_character.py、tools/export_webcam.pyを順に実行。
HTTPを内部ポート8089でdistに向けて起動し、tests/verify_revision4.py、tests/verify_repairs.py、tests/verify_face_revision.py、tests/verify_webcam_distribution.pyを実行する。tests/verify_companion_split.pyはHTTP不要。
旧0.3.0のZIPは保持。0.4.0は別名のZIP/フォルダ/HTMLで配布する。
